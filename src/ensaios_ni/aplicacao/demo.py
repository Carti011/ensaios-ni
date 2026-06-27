import math
from pathlib import Path

from ensaios_ni.aplicacao.ensaio import executar_ensaio
from ensaios_ni.aquisicao.fake import AquisicaoFake
from ensaios_ni.dominio.canais import Canais, carregar_canais

_CONFIG_EXEMPLO = Path(__file__).resolve().parents[3] / "config" / "canais.exemplo.toml"


def executar_demonstracao(
    caminho: Path,
    amostras: int = 100,
    taxa_hz: float = 100.0,
    caminho_config: Path | None = None,
) -> Path:
    """Roda um ensaio ponta a ponta no Mac, com o adaptador fake e sinal sintético.

    Não toca em hardware. Serve para ver o fluxo (ler -> converter -> gravar) funcionando
    antes de existir o adaptador real. No Windows, troca-se o fake pelo `daqmx`.
    """
    canais = carregar_canais(caminho_config or _CONFIG_EXEMPLO)
    tensoes, strains = _sinais_sinteticos(canais, amostras, taxa_hz)
    fonte = AquisicaoFake(tensoes=tensoes, strains=strains)
    executar_ensaio(fonte, canais, amostras, taxa_hz, Path(caminho))
    return Path(caminho)


def _sinais_sinteticos(
    canais: Canais, amostras: int, taxa_hz: float
) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    # senoide por tipo: tensão na faixa 0-10 V; strain ~±1e-3 adimensional (vira ±1000 µε
    # após o ganho 1e6). Cada canal recebe uma frequência levemente distinta para que o
    # gráfico XY (um canal × outro) deixe de ser uma reta fixa e evolua na tela.
    tensoes: dict[str, list[float]] = {}
    strains: dict[str, list[float]] = {}
    for indice, nome in enumerate(canais):
        freq = 2.0 + 0.05 * indice
        fase = [math.sin(2 * math.pi * freq * i / taxa_hz) for i in range(amostras)]
        if canais[nome].tipo == "strain":
            strains[nome] = [1e-3 * s for s in fase]
        else:
            tensoes[nome] = [5.0 + 5.0 * s for s in fase]
    return tensoes, strains
