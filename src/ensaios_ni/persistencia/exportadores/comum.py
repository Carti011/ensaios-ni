"""Helpers compartilhados pelos exportadores: seleção de sinais, cabeçalho e iteração."""

from collections.abc import Iterator

from ensaios_ni.dominio.metadata import Metadata
from ensaios_ni.dominio.serie import SerieTemporal

_ROTULOS_METADATA = (
    ("obra", "Obra"),
    ("operador", "Operador"),
    ("data", "Data"),
    ("observacao", "Observação"),
)


def itens_metadata(metadata: Metadata | None) -> list[tuple[str, str]]:
    """Pares (rótulo, valor) dos campos preenchidos da metadata, para o cabeçalho do laudo.

    Vazio quando `metadata` é None ou todos os campos estão em branco — aí o exportador não
    escreve cabeçalho algum (ADR-018).
    """
    if metadata is None:
        return []
    return [(rotulo, getattr(metadata, campo)) for campo, rotulo in _ROTULOS_METADATA if getattr(metadata, campo)]


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


def numero_virgula(valor: float) -> str:
    """Formata o número com decimal vírgula (padrão BR/Lynx), sem depender de locale."""
    return str(valor).replace(".", ",")


def resolver_janela(
    serie: SerieTemporal, inicio_s: float | None, fim_s: float | None
) -> range:
    """Converte a janela de tempo [inicio_s, fim_s] (inclusiva) nos índices de amostra.

    Resolve em índices (mais robusto que comparar floats) e valida cedo: recusa janela
    invertida ou que não cubra nenhuma amostra (provável engano do usuário).
    """
    if inicio_s is not None and fim_s is not None and inicio_s > fim_s:
        raise ValueError(f"janela inválida: inicio_s ({inicio_s}) > fim_s ({fim_s})")
    n_amostras = len(serie.dados[serie.canais[0]]) if serie.canais else 0
    i_inicio = 0 if inicio_s is None else max(0, round(inicio_s * serie.taxa_hz))
    i_fim = n_amostras if fim_s is None else min(n_amostras, round(fim_s * serie.taxa_hz) + 1)
    if i_inicio >= i_fim:
        raise ValueError(f"janela de tempo não contém amostras: [{inicio_s}, {fim_s}] s")
    return range(i_inicio, i_fim)


def iterar_amostras(
    serie: SerieTemporal,
    canais: list[str],
    inicio_s: float | None = None,
    fim_s: float | None = None,
) -> Iterator[tuple[float, list[float]]]:
    """Itera linha a linha: (tempo_s derivado da taxa, valores dos canais selecionados).

    `inicio_s`/`fim_s` recortam uma janela de tempo (inclusiva nas duas pontas), preservando
    o tempo absoluto — útil para exportar só um trecho de ensaios longos, que não cabem
    inteiros no Excel.
    """
    for i in resolver_janela(serie, inicio_s, fim_s):
        yield i / serie.taxa_hz, [serie.dados[c][i] for c in canais]
