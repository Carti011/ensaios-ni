"""Presenter da exportação pela UI (Fase 4, fatia 4 — ADR-015/011/012).

Python puro (testável no Mac): carrega o CSV gravado do ensaio e chama o exportador
escolhido. Espelha a CLI (`--exportar`) — a UI só desenha o diálogo e fia os eventos.
"""

from pathlib import Path

from ensaios_ni.persistencia.csv_ensaio import carregar_csv
from ensaios_ni.persistencia.exportadores import EXPORTADORES
from ensaios_ni.persistencia.metadata_ensaio import ler_metadata


class Exportacao:
    def __init__(self, caminho_csv: Path):
        self._caminho = Path(caminho_csv)

    @property
    def formatos(self) -> list[str]:
        return sorted(EXPORTADORES)

    def sinais(self) -> list[str]:
        """Canais disponíveis no ensaio gravado, para o usuário escolher o que exportar."""
        return carregar_csv(self._caminho).canais

    def exportar(
        self,
        formato: str,
        destino: Path,
        sinais: list[str] | None = None,
        inicio_s: float | None = None,
        fim_s: float | None = None,
    ) -> None:
        serie = carregar_csv(self._caminho)
        metadata = ler_metadata(self._caminho)  # cabeçalho de rastreabilidade do .meta.toml ao lado
        EXPORTADORES[formato](serie, Path(destino), sinais, inicio_s, fim_s, metadata)
