import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import tomlkit


def ler_pontos(caminho: Path, canal: str) -> list[tuple[float, float]]:
    """Pontos de calibração de um canal no TOML, ou lista vazia se ele for linear.

    O Canal carregado só guarda a reta ajustada; ao reabrir a aferição, o painel recupera os
    pontos originais daqui (a fonte da verdade é o arquivo).
    """
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    cfg = dados.get("canais", {}).get(canal, {})
    return [(float(volts), float(valor)) for volts, valor in cfg.get("pontos", [])]


def salvar_afericao(
    caminho: Path,
    canal: str,
    pontos: Sequence[tuple[float, float]],
) -> None:
    """Persiste a aferição (pontos de calibração) de um canal no TOML, preservando o resto do arquivo.

    A calibração por pontos substitui a conversão linear: ganho/offset órfãos são removidos.
    """
    pares = [[float(volts), float(valor)] for volts, valor in pontos]

    def editar(secao):
        secao["pontos"] = pares
        for campo in ("ganho", "offset"):
            secao.pop(campo, None)

    _editar_canal(caminho, canal, editar)


def salvar_rotulo(caminho: Path, canal: str, rotulo: str) -> None:
    """Persiste o rótulo (Nome do Sinal) de um canal no TOML, preservando o resto do arquivo."""
    _editar_canal(caminho, canal, lambda secao: secao.__setitem__("rotulo", rotulo))


def _editar_canal(caminho: Path, canal: str, editar: Callable[[Any], None]) -> None:
    """Lê o TOML, aplica a edição na seção do canal e regrava.

    Usa tomlkit (e não o tomllib, que só lê) para manter comentários, formatação e os demais
    canais intactos — o arquivo é editado por humano e pela UI.
    """
    caminho = Path(caminho)
    doc = tomlkit.parse(caminho.read_text(encoding="utf-8"))
    editar(doc["canais"][canal])
    caminho.write_text(tomlkit.dumps(doc), encoding="utf-8")
