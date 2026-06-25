from pathlib import Path

from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.exportadores.comum import cabecalho, iterar_amostras, selecionar


def exportar_xlsx(
    serie: SerieTemporal,
    caminho: Path,
    sinais: list[str] | None = None,
) -> None:
    """Exporta a série como `.xlsx` nativo (via openpyxl): números de verdade, não texto.

    É o "já vem no formato do Excel" que o dono valoriza (ADR-011). O Excel formata o
    decimal pelo locale do usuário, então não convertemos vírgula aqui. `openpyxl` é
    importado de forma lazy (extra opcional `[excel]`): o pacote importa sem ele.
    `sinais` seleciona quais canais entram.
    """
    from openpyxl import Workbook

    canais = selecionar(serie.canais, sinais)
    planilha = Workbook()
    aba = planilha.active
    aba.title = "Ensaio"
    aba.append(["tempo_s", *(cabecalho(c, serie.unidades) for c in canais)])
    for tempo_s, valores in iterar_amostras(serie, canais):
        aba.append([tempo_s, *valores])
    planilha.save(Path(caminho))
