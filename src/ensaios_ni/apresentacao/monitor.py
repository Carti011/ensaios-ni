from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ensaios_ni.aquisicao.porta import FonteDeAquisicao
from ensaios_ni.dominio.canais import Canais
from ensaios_ni.dominio.conversao import calcular_tara, converter
from ensaios_ni.persistencia.csv_ensaio import GravadorEnsaioCsv


class EstadoMonitor(Enum):
    PARADO = "parado"
    ADQUIRINDO = "adquirindo"
    ERRO = "erro"


class AquisicaoEmAndamento(Exception):
    """Operação só permitida com o monitor parado (ex.: recarregar a calibração durante o ensaio)."""


@dataclass(frozen=True)
class GrupoUnidade:
    """Canais que compartilham a mesma unidade — um sub-plot (eixo Y comum)."""

    unidade: str
    dados: dict[str, list[float]]


@dataclass(frozen=True)
class ParXY:
    """Um canal contra o outro (XY): carga × deformação do ensaio estático."""

    canal_x: str
    canal_y: str
    xs: list[float]
    ys: list[float]


@dataclass(frozen=True)
class QuadroAoVivo:
    """Janela atual a desenhar: tempos alinhados + valor convertido por canal."""

    tempos: list[float]
    dados: dict[str, list[float]]
    unidades: dict[str, str] = field(default_factory=dict)

    def agrupar_por_unidade(self) -> list[GrupoUnidade]:
        # empilhamento: cada unidade vira um sub-plot; µε para de achatar kgf/bar/mm
        grupos: dict[str, dict[str, list[float]]] = {}
        for canal, serie in self.dados.items():
            grupos.setdefault(self.unidades[canal], {})[canal] = serie
        return [GrupoUnidade(unidade, dados) for unidade, dados in grupos.items()]

    def par_xy(self, canal_x: str, canal_y: str) -> ParXY:
        # séries alinhadas no tempo (mesmo sample clock): ponto i de X e Y é simultâneo
        return ParXY(canal_x, canal_y, self.dados[canal_x], self.dados[canal_y])


class MonitorAoVivo:
    """Presenter do monitor ao vivo (Fase 4, fatia 1 — ADR-015).

    Máquina de passos sem dono de thread: o widget liga `QTimer → passo()`; os
    testes chamam `passo()` num laço. Consome a porta `FonteDeAquisicao`, converte
    cada bloco e mantém a janela de visualização — sem importar PySide.
    """

    def __init__(
        self,
        fonte: FonteDeAquisicao,
        canais: Canais,
        taxa_hz: float,
        amostras_por_bloco: int,
        caminho: Path,
        capacidade_janela: int | None = None,
    ):
        self._fonte = fonte
        self._canais = canais
        self._nomes = list(canais)
        self._unidades = {nome: canais[nome].unidade for nome in self._nomes}
        self._taxa_hz = taxa_hz
        self._bloco = amostras_por_bloco
        self._caminho = Path(caminho)
        self._estado = EstadoMonitor.PARADO
        self._fluxos: list = []
        self._gravador: GravadorEnsaioCsv | None = None
        self._erro: str | None = None
        self._indice = 0
        self._gravou = False  # houve ensaio gravado nesta sessão? (habilita o exportar)
        self._taras: dict[str, float] = {}
        self._zerar_pendente = False
        self._tempos: deque[float] = deque(maxlen=capacidade_janela)
        self._dados: dict[str, deque[float]] = {
            nome: deque(maxlen=capacidade_janela) for nome in self._nomes
        }

    @property
    def estado(self) -> EstadoMonitor:
        return self._estado

    @property
    def erro(self) -> str | None:
        return self._erro

    @property
    def caminho(self) -> Path:
        """Arquivo CSV onde o ensaio é gravado (origem da exportação pela UI)."""
        return self._caminho

    @property
    def tem_ensaio(self) -> bool:
        """Houve ensaio gravado nesta sessão — não confundir com um CSV residual em disco."""
        return self._gravou

    def iniciar(self) -> None:
        self._reiniciar_janela()
        self._gravador = GravadorEnsaioCsv(
            self._caminho, self._nomes, self._taxa_hz, self._unidades
        )
        self._gravador.__enter__()
        self._fluxos = self._abrir_fluxos()
        self._estado = EstadoMonitor.ADQUIRINDO

    def passo(self) -> bool:
        try:
            partes = [next(fluxo) for fluxo in self._fluxos]
        except StopIteration:
            self.parar()
            return False
        except Exception as erro:  # falha de aquisição: encerra limpo, sem vazar traceback
            self._erro = str(erro)
            self._fechar_gravador()
            self._fluxos = []
            self._estado = EstadoMonitor.ERRO
            return False
        bloco: dict[str, list[float]] = {}
        for parte in partes:
            bloco.update(parte)
        if self._zerar_pendente:  # Zero Channel: este bloco de repouso vira o zero dos canais
            self._taras = {
                nome: calcular_tara(bloco[nome], self._canais[nome]) for nome in self._nomes
            }
            self._zerar_pendente = False
        convertido = {
            nome: [
                converter(v, self._canais[nome], tara=self._taras.get(nome, 0.0))
                for v in bloco[nome]
            ]
            for nome in self._nomes
        }
        self._gravador.escrever_bloco(convertido)
        self._gravou = True
        for i in range(len(convertido[self._nomes[0]])):
            self._tempos.append(self._indice / self._taxa_hz)
            for nome in self._nomes:
                self._dados[nome].append(convertido[nome][i])
            self._indice += 1
        return True

    def parar(self) -> None:
        self._fechar_gravador()
        self._fluxos = []
        self._estado = EstadoMonitor.PARADO

    def zerar(self) -> None:
        """Tara (Zero Channel): o próximo bloco de repouso vira o zero dos canais."""
        self._zerar_pendente = True

    def ler_tensao_atual(self, canal: str, amostras: int = 100) -> float:
        """Tensão crua (volts) do canal, média de uma leitura curta — o "Leitura do A/D" da aferição.

        Sem conversão de propósito: a aferição mapeia volts -> unidade, então precisa dos volts crus.
        """
        leitura = self._fonte.ler_tensao([canal], amostras, self._taxa_hz)[canal]
        return sum(leitura) / len(leitura)

    def recarregar_canais(self, canais: Canais) -> None:
        """Troca a calibração (após aferir e aplicar); vale do próximo Iniciar.

        Calibração é etapa pré-ensaio: durante a aquisição ela fica fixa para o laudo ter
        rastreabilidade, então recarregar adquirindo é recusado.
        """
        if self._estado is EstadoMonitor.ADQUIRINDO:
            raise AquisicaoEmAndamento("não recarregue a calibração durante a aquisição")
        self._canais = canais

    def _fechar_gravador(self) -> None:
        if self._gravador is not None:
            self._gravador.__exit__(None, None, None)
            self._gravador = None

    def _reiniciar_janela(self) -> None:
        # cada iniciar é um ensaio novo: tempo do zero e janela limpa (o CSV é sobrescrito)
        self._erro = None
        self._indice = 0
        self._taras = {}  # tara é por-ensaio: cada Iniciar recomeça sem zero
        self._zerar_pendente = False
        self._tempos.clear()
        for janela in self._dados.values():
            janela.clear()

    def _abrir_fluxos(self) -> list:
        """Um fluxo de streaming por tipo de canal presente (tensão e/ou strain)."""
        tensao = [nome for nome in self._nomes if self._canais[nome].tipo == "tensao"]
        strain = [nome for nome in self._nomes if self._canais[nome].tipo == "strain"]
        fluxos = []
        if tensao:
            fluxos.append(self._fonte.transmitir_tensao(tensao, self._taxa_hz, self._bloco))
        if strain:
            fluxos.append(self._fonte.transmitir_strain(strain, self._taxa_hz, self._bloco))
        return fluxos

    def valor_atual(self, canal: str) -> float | None:
        janela = self._dados[canal]
        return janela[-1] if janela else None

    def quadro(self) -> QuadroAoVivo:
        return QuadroAoVivo(
            tempos=list(self._tempos),
            dados={nome: list(self._dados[nome]) for nome in self._nomes},
            unidades=dict(self._unidades),
        )
