from pathlib import Path

from ensaios_ni.dominio.metadata import Metadata
from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.exportadores.comum import (
    cabecalho,
    itens_metadata,
    iterar_amostras,
    selecionar,
)


def exportar_xlsx(
    serie: SerieTemporal,
    caminho: Path,
    sinais: list[str] | None = None,
    inicio_s: float | None = None,
    fim_s: float | None = None,
    metadata: Metadata | None = None,
) -> None:
    """Exporta a série como `.xlsx` nativo (via openpyxl): números de verdade, não texto.

    É o "já vem no formato do Excel" que o dono valoriza (ADR-011). O Excel formata o
    decimal pelo locale do usuário, então não convertemos vírgula aqui. `openpyxl` é
    importado de forma lazy (extra opcional `[excel]`): o pacote importa sem ele.
    `sinais` seleciona quais canais entram; `inicio_s`/`fim_s` recortam um trecho.
    `metadata`, quando preenchida, vira um cabeçalho de rastreabilidade no topo (ADR-018).
    """
    from openpyxl import Workbook

    canais = selecionar(serie.canais, sinais)
    planilha = Workbook()
    aba = planilha.active
    aba.title = "Ensaio"
    itens = itens_metadata(metadata)
    for rotulo, valor in itens:  # cabeçalho de laudo (se houver)
        aba.append([rotulo, valor])
    if itens:
        aba.append([])  # linha em branco separa a metadata dos dados
    aba.append(["tempo_s", *(cabecalho(c, serie.unidades) for c in canais)])
    for tempo_s, valores in iterar_amostras(serie, canais, inicio_s, fim_s):
        aba.append([tempo_s, *valores])
    planilha.save(Path(caminho))
