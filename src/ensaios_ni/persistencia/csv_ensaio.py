import csv
from pathlib import Path


def gravar_ensaio(
    caminho: Path,
    amostras_por_canal: dict[str, list[float]],
    taxa_hz: float,
    unidades: dict[str, str] | None = None,
) -> None:
    """Grava um ensaio em CSV: coluna de tempo + uma coluna por canal.

    `unidades` (opcional) anexa a unidade no cabeçalho: `Mod1/ai0 (kgf)`.
    """
    if taxa_hz <= 0:
        raise ValueError(f"taxa_hz deve ser > 0, recebido {taxa_hz}")
    canais = list(amostras_por_canal)
    n_amostras = len(amostras_por_canal[canais[0]])
    if any(len(amostras_por_canal[c]) != n_amostras for c in canais):
        contagens = {c: len(amostras_por_canal[c]) for c in canais}
        raise ValueError(f"todos os canais devem ter o mesmo número de amostras: {contagens}")
    unidades = unidades or {}
    with Path(caminho).open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(["tempo_s", *(_cabecalho(c, unidades) for c in canais)])
        for i in range(n_amostras):
            tempo_s = i / taxa_hz
            escritor.writerow([tempo_s, *(amostras_por_canal[c][i] for c in canais)])


def _cabecalho(canal: str, unidades: dict[str, str]) -> str:
    unidade = unidades.get(canal)
    return f"{canal} ({unidade})" if unidade else canal
