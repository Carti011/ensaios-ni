from ensaios_ni.aquisicao.porta import FonteDeAquisicao


class AquisicaoFake(FonteDeAquisicao):
    """Adaptador sintético da porta. Devolve tensões pré-definidas por canal."""

    def __init__(self, tensoes: dict[str, list[float]]):
        self._tensoes = tensoes

    def ler_tensao(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        if amostras <= 0:
            raise ValueError(f"amostras deve ser > 0, recebido {amostras}")
        if taxa_hz <= 0:
            raise ValueError(f"taxa_hz deve ser > 0, recebido {taxa_hz}")
        leituras: dict[str, list[float]] = {}
        for canal in canais:
            if canal not in self._tensoes:
                raise ValueError(f"canal '{canal}' não tem dados sintéticos no fake")
            disponiveis = self._tensoes[canal]
            if amostras > len(disponiveis):
                raise ValueError(
                    f"canal '{canal}' tem {len(disponiveis)} amostras, pedidas {amostras}"
                )
            leituras[canal] = disponiveis[:amostras]
        return leituras
