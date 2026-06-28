"""Persistência da metadata do ensaio num arquivo paralelo ao CSV — ADR-018.

`ensaio.csv` ↔ `ensaio.meta.toml`: o ensaio é um par (dados + rastreabilidade), mantendo o CSV
"wide" (ADR-003) e o `carregar_csv` intactos.
"""

import tomllib
from dataclasses import asdict, fields
from pathlib import Path

import tomlkit

from ensaios_ni.dominio.metadata import Metadata


def caminho_metadata(caminho_csv: Path) -> Path:
    """Arquivo de metadata ao lado do CSV: ensaio.csv -> ensaio.meta.toml."""
    return Path(caminho_csv).with_suffix(".meta.toml")


def gravar_metadata(caminho_csv: Path, metadata: Metadata) -> None:
    doc = tomlkit.document()
    doc["ensaio"] = asdict(metadata)
    caminho_metadata(caminho_csv).write_text(tomlkit.dumps(doc), encoding="utf-8")


def ler_metadata(caminho_csv: Path) -> Metadata:
    """Metadata do ensaio, ou uma vazia quando o arquivo paralelo não existe."""
    caminho = caminho_metadata(caminho_csv)
    if not caminho.exists():
        return Metadata()
    secao = tomllib.loads(caminho.read_text(encoding="utf-8")).get("ensaio", {})
    campos = {f.name for f in fields(Metadata)}
    return Metadata(**{k: v for k, v in secao.items() if k in campos})
