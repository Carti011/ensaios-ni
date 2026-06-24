from pathlib import Path

from ensaios_ni.aquisicao.porta import FonteDeAquisicao
from ensaios_ni.dominio.canais import Canais
from ensaios_ni.dominio.conversao import calcular_tara, converter
from ensaios_ni.persistencia.csv_ensaio import gravar_ensaio


def executar_ensaio(
    fonte: FonteDeAquisicao,
    canais: Canais,
    amostras: int,
    taxa_hz: float,
    caminho: Path,
    amostras_tara: int = 0,
) -> None:
    """Lê os canais configurados, converte para unidade de engenharia e grava em CSV.

    Se `amostras_tara > 0`, faz antes uma leitura de repouso e usa a média como
    tara (zero) de cada canal — o "Zero Channel" do fluxo do dono.
    """
    nomes = list(canais)
    taras = _capturar_taras(fonte, canais, nomes, amostras_tara, taxa_hz)
    leituras = fonte.ler_tensao(nomes, amostras, taxa_hz)
    valores_por_canal: dict[str, list[float]] = {}
    unidades: dict[str, str] = {}
    for nome in nomes:
        canal = canais[nome]
        valores_por_canal[nome] = [converter(v, canal, tara=taras[nome]) for v in leituras[nome]]
        unidades[nome] = canal.unidade
    gravar_ensaio(caminho, valores_por_canal, taxa_hz, unidades)


def _capturar_taras(
    fonte: FonteDeAquisicao,
    canais: Canais,
    nomes: list[str],
    amostras_tara: int,
    taxa_hz: float,
) -> dict[str, float]:
    if amostras_tara <= 0:
        return {nome: 0.0 for nome in nomes}
    repouso = fonte.ler_tensao(nomes, amostras_tara, taxa_hz)
    return {nome: calcular_tara(repouso[nome], canais[nome]) for nome in nomes}
