from dataclasses import dataclass, field


@dataclass(frozen=True)
class SerieTemporal:
    """Série temporal de um ensaio: a moeda comum entre quem produz e quem exporta.

    Resultado já convertido (unidade de engenharia), no layout "wide" do ADR-003:
    `canais` na ordem do config, `unidades` (canal -> unidade), `taxa_hz` e
    `dados` (canal -> lista de valores). Vem da memória (ensaio finito) ou de um
    CSV gravado (`carregar_csv`). Imutável e sem dependência de aquisição (ADR-012).
    """

    canais: list[str]
    unidades: dict[str, str]
    taxa_hz: float
    dados: dict[str, list[float]] = field(default_factory=dict)

    def __post_init__(self):
        if self.taxa_hz <= 0:
            raise ValueError(f"taxa_hz deve ser > 0, recebido {self.taxa_hz}")
        if self.canais:
            n_amostras = len(self.dados[self.canais[0]])
            if any(len(self.dados[c]) != n_amostras for c in self.canais):
                contagens = {c: len(self.dados[c]) for c in self.canais}
                raise ValueError(
                    f"todos os canais devem ter o mesmo número de amostras: {contagens}"
                )
