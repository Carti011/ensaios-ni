from pathlib import Path

from ensaios_ni.aquisicao.porta import FonteDeAquisicao
from ensaios_ni.dominio.canais import Canais
from ensaios_ni.dominio.conversao import converter
from ensaios_ni.persistencia.csv_ensaio import gravar_ensaio


def executar_ensaio(
    fonte: FonteDeAquisicao,
    canais: Canais,
    amostras: int,
    taxa_hz: float,
    caminho: Path,
) -> None:
    """Lê cada canal configurado, converte para unidade de engenharia e grava em CSV."""
    valores_por_canal: dict[str, list[float]] = {}
    unidades: dict[str, str] = {}
    for nome in canais:
        canal = canais[nome]
        volts = fonte.ler_tensao(nome, amostras)
        valores_por_canal[nome] = [converter(v, canal) for v in volts]
        unidades[nome] = canal.unidade
    gravar_ensaio(caminho, valores_por_canal, taxa_hz, unidades)
