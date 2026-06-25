"""Helpers compartilhados pelos exportadores: seleção de sinais, cabeçalho e iteração."""

from collections.abc import Iterator

from ensaios_ni.dominio.serie import SerieTemporal


def selecionar(canais: list[str], sinais: list[str] | None) -> list[str]:
    """Filtra os canais a exportar, preservando a ordem do config. `None` = todos."""
    if sinais is None:
        return canais
    desconhecidos = [s for s in sinais if s not in canais]
    if desconhecidos:
        raise ValueError(f"sinais inexistentes na série: {desconhecidos}")
    return [c for c in canais if c in sinais]


def cabecalho(canal: str, unidades: dict[str, str]) -> str:
    """Monta o rótulo da coluna: `Canal (unidade)` quando há unidade, senão `Canal`."""
    unidade = unidades.get(canal)
    return f"{canal} ({unidade})" if unidade else canal


def iterar_amostras(
    serie: SerieTemporal, canais: list[str]
) -> Iterator[tuple[float, list[float]]]:
    """Itera linha a linha: (tempo_s derivado da taxa, valores dos canais selecionados)."""
    n_amostras = len(serie.dados[serie.canais[0]]) if serie.canais else 0
    for i in range(n_amostras):
        yield i / serie.taxa_hz, [serie.dados[c][i] for c in canais]
