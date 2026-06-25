import csv
import re
from pathlib import Path

from ensaios_ni.dominio.serie import SerieTemporal


class GravadorEnsaioCsv:
    """Grava um ensaio em CSV de forma incremental (append por bloco).

    Mantém o arquivo aberto e escreve o cabeçalho uma vez; cada `escrever_bloco`
    adiciona linhas continuando a coluna de tempo (índice de amostra global), sem
    acumular tudo em memória — para aquisição contínua de longa duração (ADR-007).
    Usar como context manager para garantir o fechamento do arquivo.
    """

    def __init__(
        self,
        caminho: Path,
        canais: list[str],
        taxa_hz: float,
        unidades: dict[str, str] | None = None,
    ):
        if taxa_hz <= 0:
            raise ValueError(f"taxa_hz deve ser > 0, recebido {taxa_hz}")
        self._caminho = Path(caminho)
        self._canais = list(canais)
        self._taxa_hz = taxa_hz
        self._unidades = unidades or {}
        self._indice = 0
        self._arquivo = None
        self._escritor = None

    def __enter__(self) -> "GravadorEnsaioCsv":
        self._arquivo = self._caminho.open("w", encoding="utf-8", newline="")
        self._escritor = csv.writer(self._arquivo, lineterminator="\n")
        self._escritor.writerow(["tempo_s", *(_cabecalho(c, self._unidades) for c in self._canais)])
        return self

    def escrever_bloco(self, amostras_por_canal: dict[str, list[float]]) -> None:
        n_amostras = _validar_contagens_iguais(amostras_por_canal, self._canais)
        for i in range(n_amostras):
            tempo_s = self._indice / self._taxa_hz
            self._escritor.writerow([tempo_s, *(amostras_por_canal[c][i] for c in self._canais)])
            self._indice += 1

    def __exit__(self, *exc) -> bool:
        if self._arquivo is not None:
            self._arquivo.close()
        return False


def gravar_ensaio(
    caminho: Path,
    amostras_por_canal: dict[str, list[float]],
    taxa_hz: float,
    unidades: dict[str, str] | None = None,
) -> None:
    """Grava um ensaio em CSV de uma vez (o caso de um único bloco).

    `unidades` (opcional) anexa a unidade no cabeçalho: `Mod1/ai0 (kgf)`.
    """
    canais = list(amostras_por_canal)
    _validar_contagens_iguais(amostras_por_canal, canais)  # falha cedo, sem criar arquivo
    with GravadorEnsaioCsv(caminho, canais, taxa_hz, unidades) as gravador:
        gravador.escrever_bloco(amostras_por_canal)


def carregar_csv(caminho: Path) -> SerieTemporal:
    """Lê um CSV "wide" (ADR-003) de volta para uma SerieTemporal (inverso de gravar_ensaio).

    Reconstrói as unidades do cabeçalho `Canal (unidade)` e deriva a `taxa_hz` das
    duas primeiras marcas de `tempo_s`. Habilita reexportar ensaios já gravados (ADR-012).
    """
    with Path(caminho).open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor)
        linhas = [linha for linha in leitor if linha]

    canais, unidades = _parsear_cabecalho(cabecalho[1:])
    if len(linhas) < 2:
        raise ValueError("CSV precisa de ao menos 2 amostras para derivar a taxa de amostragem")
    taxa_hz = 1.0 / (float(linhas[1][0]) - float(linhas[0][0]))

    dados: dict[str, list[float]] = {canal: [] for canal in canais}
    for linha in linhas:
        for indice, canal in enumerate(canais, start=1):
            dados[canal].append(float(linha[indice]))
    return SerieTemporal(canais=canais, unidades=unidades, taxa_hz=taxa_hz, dados=dados)


_CABECALHO_COM_UNIDADE = re.compile(r"^(.*) \((.*)\)$")


def _parsear_cabecalho(colunas: list[str]) -> tuple[list[str], dict[str, str]]:
    canais: list[str] = []
    unidades: dict[str, str] = {}
    for coluna in colunas:
        casamento = _CABECALHO_COM_UNIDADE.match(coluna)
        if casamento:
            canal, unidade = casamento.group(1), casamento.group(2)
            unidades[canal] = unidade
        else:
            canal = coluna
        canais.append(canal)
    return canais, unidades


def _validar_contagens_iguais(amostras_por_canal: dict[str, list[float]], canais: list[str]) -> int:
    n_amostras = len(amostras_por_canal[canais[0]])
    if any(len(amostras_por_canal[c]) != n_amostras for c in canais):
        contagens = {c: len(amostras_por_canal[c]) for c in canais}
        raise ValueError(f"todos os canais devem ter o mesmo número de amostras: {contagens}")
    return n_amostras


def _cabecalho(canal: str, unidades: dict[str, str]) -> str:
    unidade = unidades.get(canal)
    return f"{canal} ({unidade})" if unidade else canal
