import tomllib
from dataclasses import dataclass
from pathlib import Path

from ensaios_ni.dominio.erros import (
    CanalNaoConfigurado,
    ConfiguracaoInvalida,
    RegressaoIndeterminada,
)
from ensaios_ni.dominio.regressao import Reta, ajustar_regressao

CAMPOS_BASE = ("tipo", "unidade")
TIPOS_VALIDOS = ("tensao", "strain")
METODOS_VALIDOS = ("regressao", "segmento")
METODO_PADRAO = "regressao"


@dataclass(frozen=True)
class Canal:
    """Canal físico e sua conversão: por pontos de calibração ou linear (ganho/offset)."""

    nome: str
    tipo: str
    unidade: str
    ganho: float | None = None
    offset: float | None = None
    pontos: tuple[tuple[float, float], ...] | None = None
    reta: Reta | None = None
    rotulo: str | None = None

    @property
    def etiqueta(self) -> str:
        """Nome a exibir: o rótulo humano, ou o endereço físico quando não há rótulo."""
        return self.rotulo or self.nome


class Canais:
    """Coleção de canais. Acesso por nome levanta erro de domínio se ausente."""

    def __init__(self, por_nome: dict[str, Canal]):
        self._por_nome = por_nome

    def __getitem__(self, nome: str) -> Canal:
        try:
            return self._por_nome[nome]
        except KeyError:
            raise CanalNaoConfigurado(nome) from None

    def __contains__(self, nome: str) -> bool:
        return nome in self._por_nome

    def __iter__(self):
        return iter(self._por_nome)

    def __len__(self) -> int:
        return len(self._por_nome)


def carregar_canais(caminho: Path) -> Canais:
    """Lê o mapeamento canal -> conversão de um arquivo TOML, validando cada canal."""
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    return Canais({nome: _construir_canal(nome, cfg) for nome, cfg in dados.get("canais", {}).items()})


def _construir_canal(nome: str, cfg: dict) -> Canal:
    faltando = [campo for campo in CAMPOS_BASE if campo not in cfg]
    if faltando:
        raise ConfiguracaoInvalida(f"canal '{nome}': campos obrigatórios faltando: {', '.join(faltando)}")
    if cfg["tipo"] not in TIPOS_VALIDOS:
        raise ConfiguracaoInvalida(
            f"canal '{nome}': tipo '{cfg['tipo']}' inválido (use {' ou '.join(TIPOS_VALIDOS)})"
        )
    rotulo = _rotulo(nome, cfg)
    if "pontos" in cfg:
        return _canal_calibrado(nome, cfg, rotulo)
    if "metodo" in cfg:
        raise ConfiguracaoInvalida(f"canal '{nome}': 'metodo' só se aplica quando há 'pontos'")
    faltando = [campo for campo in ("ganho", "offset") if campo not in cfg]
    if faltando:
        raise ConfiguracaoInvalida(
            f"canal '{nome}': informe 'pontos' de calibração ou 'ganho'/'offset' "
            f"(faltando: {', '.join(faltando)})"
        )
    return Canal(
        nome=nome,
        tipo=cfg["tipo"],
        unidade=cfg["unidade"],
        rotulo=rotulo,
        ganho=_numero(nome, "ganho", cfg["ganho"]),
        offset=_numero(nome, "offset", cfg["offset"]),
    )


def _canal_calibrado(nome: str, cfg: dict, rotulo: str | None) -> Canal:
    """Canal com tabela de pontos: regressão linear (default, à la AqDados) ou segmento (opt-in)."""
    metodo = cfg.get("metodo", METODO_PADRAO)
    if metodo not in METODOS_VALIDOS:
        raise ConfiguracaoInvalida(
            f"canal '{nome}': metodo '{metodo}' inválido (use {' ou '.join(METODOS_VALIDOS)})"
        )
    pares = _parsear_pares(nome, cfg["pontos"])
    base = dict(nome=nome, tipo=cfg["tipo"], unidade=cfg["unidade"], rotulo=rotulo)
    if metodo == "segmento":
        return Canal(**base, pontos=_preparar_segmento(nome, pares))
    try:
        return Canal(**base, reta=ajustar_regressao(pares))
    except RegressaoIndeterminada as erro:
        raise ConfiguracaoInvalida(f"canal '{nome}': {erro}") from None


def _parsear_pares(nome: str, valor) -> list[tuple[float, float]]:
    if not isinstance(valor, list) or len(valor) < 2:
        raise ConfiguracaoInvalida(f"canal '{nome}': 'pontos' precisa de ao menos 2 pares [volts, valor]")
    pares = []
    for item in valor:
        if not isinstance(item, list) or len(item) != 2:
            raise ConfiguracaoInvalida(f"canal '{nome}': cada ponto deve ser um par [volts, valor], recebido {item!r}")
        pares.append((_numero(nome, "pontos", item[0]), _numero(nome, "pontos", item[1])))
    return pares


def _preparar_segmento(nome: str, pares: list[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    # interpolação por segmento exige volts ordenado e único (curva sem ambiguidade)
    ordenados = sorted(pares, key=lambda par: par[0])
    if len({volts for volts, _ in ordenados}) != len(ordenados):
        raise ConfiguracaoInvalida(f"canal '{nome}': há pontos com o mesmo valor de volts (curva ambígua)")
    return tuple(ordenados)


def _rotulo(nome: str, cfg: dict) -> str | None:
    rotulo = cfg.get("rotulo")
    if rotulo is not None and not isinstance(rotulo, str):
        raise ConfiguracaoInvalida(f"canal '{nome}': campo 'rotulo' deve ser texto, recebido {rotulo!r}")
    return rotulo


def _numero(nome: str, campo: str, valor) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfiguracaoInvalida(f"canal '{nome}': campo '{campo}' deve ser número, recebido {valor!r}")
    return float(valor)
