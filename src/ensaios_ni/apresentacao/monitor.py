from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ensaios_ni.aquisicao.porta import FonteDeAquisicao
from ensaios_ni.dominio.canais import Canais
from ensaios_ni.dominio.conversao import converter
from ensaios_ni.persistencia.csv_ensaio import GravadorEnsaioCsv


class EstadoMonitor(Enum):
    PARADO = "parado"
    ADQUIRINDO = "adquirindo"
    ERRO = "erro"


@dataclass(frozen=True)
class GrupoUnidade:
    """Canais que compartilham a mesma unidade — um sub-plot (eixo Y comum)."""

    unidade: str
    dados: dict[str, list[float]]


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
        convertido = {
            nome: [converter(v, self._canais[nome]) for v in bloco[nome]] for nome in self._nomes
        }
        self._gravador.escrever_bloco(convertido)
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

    def _fechar_gravador(self) -> None:
        if self._gravador is not None:
            self._gravador.__exit__(None, None, None)
            self._gravador = None

    def _reiniciar_janela(self) -> None:
        # cada iniciar é um ensaio novo: tempo do zero e janela limpa (o CSV é sobrescrito)
        self._erro = None
        self._indice = 0
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
