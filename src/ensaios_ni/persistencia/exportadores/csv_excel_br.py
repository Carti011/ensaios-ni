from pathlib import Path

from ensaios_ni.dominio.metadata import Metadata
from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.exportadores.comum import (
    cabecalho,
    itens_metadata,
    iterar_amostras,
    numero_virgula,
    resolver_janela,
    selecionar,
)


def exportar_csv_excel_br(
    serie: SerieTemporal,
    caminho: Path,
    sinais: list[str] | None = None,
    inicio_s: float | None = None,
    fim_s: float | None = None,
    metadata: Metadata | None = None,
) -> None:
    """Exporta a série como CSV amigável ao Excel BR: separador `;` e decimal vírgula.

    No Excel em português o separador de lista é `;` e o decimal é `,`; um CSV com
    `,`/`.` abriria tudo numa coluna só (ADR-011). Grava com BOM (utf-8-sig) para o
    Excel reconhecer os acentos das unidades. `sinais` seleciona quais canais entram;
    `inicio_s`/`fim_s` recortam uma janela de tempo (trecho do ensaio). `metadata`, quando
    preenchida, vira um cabeçalho de rastreabilidade no topo do laudo (ADR-018).
    """
    canais = selecionar(serie.canais, sinais)
    resolver_janela(serie, inicio_s, fim_s)  # valida cedo, antes de criar o arquivo
    with Path(caminho).open("w", encoding="utf-8-sig", newline="") as arquivo:
        for rotulo, valor in itens_metadata(metadata):  # cabeçalho de laudo (se houver)
            arquivo.write(_linha([rotulo, valor]))
        if itens_metadata(metadata):
            arquivo.write("\n")  # linha em branco separa a metadata dos dados
        arquivo.write(_linha(["tempo_s", *(cabecalho(c, serie.unidades) for c in canais)]))
        for tempo_s, valores in iterar_amostras(serie, canais, inicio_s, fim_s):
            arquivo.write(_linha([numero_virgula(tempo_s), *(numero_virgula(v) for v in valores)]))


def _linha(campos: list[str]) -> str:
    return ";".join(campos) + "\n"
