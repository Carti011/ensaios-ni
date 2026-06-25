from pathlib import Path

from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.exportadores.comum import (
    cabecalho,
    iterar_amostras,
    numero_virgula,
    resolver_janela,
    selecionar,
)

# PROVISÓRIO — formato a calibrar com um TXT autêntico do AqDAnalysis ou um teste de importação
# no Windows (ADR-011). Só o decimal vírgula é confirmado (telas do Lynx mostram "1,2241"); o
# separador TAB, o encoding utf-8 e o cabeçalho de uma linha são as escolhas mais defensáveis,
# mas são os pontos prováveis de ajuste. Mudar qualquer um deles é trivial (não muda a estrutura).
_SEPARADOR = "\t"


def exportar_txt_aqanalysis(
    serie: SerieTemporal,
    caminho: Path,
    sinais: list[str] | None = None,
    inicio_s: float | None = None,
    fim_s: float | None = None,
) -> None:
    """Exporta a série como TXT para o "Importa Arquivo Texto" do AqDAnalysis (ADR-011).

    Decimal vírgula (padrão Lynx) e colunas separadas por TAB, com uma linha de cabeçalho
    (`tempo_s` + `Canal (unidade)`). `sinais` e `inicio_s`/`fim_s` selecionam canais e trecho.
    **Provisório:** o layout exato do AqDAnalysis ainda não foi validado — ver nota acima.
    """
    canais = selecionar(serie.canais, sinais)
    resolver_janela(serie, inicio_s, fim_s)  # valida cedo, antes de criar o arquivo
    with Path(caminho).open("w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(_linha(["tempo_s", *(cabecalho(c, serie.unidades) for c in canais)]))
        for tempo_s, valores in iterar_amostras(serie, canais, inicio_s, fim_s):
            arquivo.write(_linha([numero_virgula(tempo_s), *(numero_virgula(v) for v in valores)]))


def _linha(campos: list[str]) -> str:
    return _SEPARADOR.join(campos) + "\n"
