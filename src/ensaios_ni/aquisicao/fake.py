from ensaios_ni.aquisicao.porta import FonteDeAquisicao


class AquisicaoFake(FonteDeAquisicao):
    """Adaptador sintético da porta. Devolve tensões e strain pré-definidos por canal."""

    def __init__(
        self,
        tensoes: dict[str, list[float]] | None = None,
        strains: dict[str, list[float]] | None = None,
    ):
        self._tensoes = tensoes or {}
        self._strains = strains or {}

    def ler_tensao(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        return self._ler(self._tensoes, canais, amostras, taxa_hz)

    def ler_strain(
        self, canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        return self._ler(self._strains, canais, amostras, taxa_hz)

    @staticmethod
    def _ler(
        fonte: dict[str, list[float]], canais: list[str], amostras: int, taxa_hz: float
    ) -> dict[str, list[float]]:
        if amostras <= 0:
            raise ValueError(f"amostras deve ser > 0, recebido {amostras}")
        if taxa_hz <= 0:
            raise ValueError(f"taxa_hz deve ser > 0, recebido {taxa_hz}")
        leituras: dict[str, list[float]] = {}
        for canal in canais:
            if canal not in fonte:
                raise ValueError(f"canal '{canal}' não tem dados sintéticos no fake")
            disponiveis = fonte[canal]
            if amostras > len(disponiveis):
                raise ValueError(
                    f"canal '{canal}' tem {len(disponiveis)} amostras, pedidas {amostras}"
                )
            leituras[canal] = disponiveis[:amostras]
        return leituras
