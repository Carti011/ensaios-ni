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
    """Lê os canais configurados (tensão e/ou strain), converte e grava em CSV.

    Tensão (9205) e strain (9235) são lidos em tasks separadas (tipos de medição
    diferentes) e gravados juntos, na ordem em que aparecem no config. Se
    `amostras_tara > 0`, faz antes uma leitura de repouso e usa a média como tara
    (zero) de cada canal — o "Zero Channel" do fluxo do dono.
    """
    nomes = list(canais)
    taras = _capturar_taras(fonte, canais, nomes, amostras_tara, taxa_hz)
    leituras = _ler_por_tipo(fonte, canais, nomes, amostras, taxa_hz)
    valores_por_canal: dict[str, list[float]] = {}
    unidades: dict[str, str] = {}
    for nome in nomes:
        canal = canais[nome]
        valores_por_canal[nome] = [converter(v, canal, tara=taras[nome]) for v in leituras[nome]]
        unidades[nome] = canal.unidade
    gravar_ensaio(caminho, valores_por_canal, taxa_hz, unidades)


def _ler_por_tipo(
    fonte: FonteDeAquisicao,
    canais: Canais,
    nomes: list[str],
    amostras: int,
    taxa_hz: float,
) -> dict[str, list[float]]:
    """Particiona os canais por tipo e lê cada grupo na sua task, combinando o resultado."""
    tensao = [nome for nome in nomes if canais[nome].tipo == "tensao"]
    strain = [nome for nome in nomes if canais[nome].tipo == "strain"]
    leituras: dict[str, list[float]] = {}
    if tensao:
        leituras.update(fonte.ler_tensao(tensao, amostras, taxa_hz))
    if strain:
        leituras.update(fonte.ler_strain(strain, amostras, taxa_hz))
    return leituras


def _capturar_taras(
    fonte: FonteDeAquisicao,
    canais: Canais,
    nomes: list[str],
    amostras_tara: int,
    taxa_hz: float,
) -> dict[str, float]:
    if amostras_tara <= 0:
        return {nome: 0.0 for nome in nomes}
    repouso = _ler_por_tipo(fonte, canais, nomes, amostras_tara, taxa_hz)
    return {nome: calcular_tara(repouso[nome], canais[nome]) for nome in nomes}
