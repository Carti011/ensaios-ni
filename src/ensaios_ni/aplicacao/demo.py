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
    fonte = AquisicaoFake(_sinal_sintetico(canais, amostras, taxa_hz))
    executar_ensaio(fonte, canais, amostras, taxa_hz, Path(caminho))
    return Path(caminho)


def _sinal_sintetico(canais: Canais, amostras: int, taxa_hz: float) -> dict[str, list[float]]:
    # senoide de 2 Hz na faixa 0-10 V, simulando um ensaio dinâmico
    return {
        nome: [5.0 + 5.0 * math.sin(2 * math.pi * 2.0 * i / taxa_hz) for i in range(amostras)]
        for nome in canais
    }
