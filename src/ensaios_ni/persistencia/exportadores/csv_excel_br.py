from pathlib import Path

from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.exportadores.comum import (
    cabecalho,
    iterar_amostras,
    resolver_janela,
    selecionar,
)


def exportar_csv_excel_br(
    serie: SerieTemporal,
    caminho: Path,
    sinais: list[str] | None = None,
    inicio_s: float | None = None,
    fim_s: float | None = None,
) -> None:
    """Exporta a série como CSV amigável ao Excel BR: separador `;` e decimal vírgula.

    No Excel em português o separador de lista é `;` e o decimal é `,`; um CSV com
    `,`/`.` abriria tudo numa coluna só (ADR-011). Grava com BOM (utf-8-sig) para o
    Excel reconhecer os acentos das unidades. `sinais` seleciona quais canais entram;
    `inicio_s`/`fim_s` recortam uma janela de tempo (trecho do ensaio).
    """
    canais = selecionar(serie.canais, sinais)
    resolver_janela(serie, inicio_s, fim_s)  # valida cedo, antes de criar o arquivo
    with Path(caminho).open("w", encoding="utf-8-sig", newline="") as arquivo:
        arquivo.write(_linha(["tempo_s", *(cabecalho(c, serie.unidades) for c in canais)]))
        for tempo_s, valores in iterar_amostras(serie, canais, inicio_s, fim_s):
            arquivo.write(_linha([_numero(tempo_s), *(_numero(v) for v in valores)]))


def _linha(campos: list[str]) -> str:
    return ";".join(campos) + "\n"


def _numero(valor: float) -> str:
    return str(valor).replace(".", ",")
