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
class ParametrosStrain:
    """Parâmetros físicos do extensômetro no 9235, por canal.

    Os DEFAULTS são os do 9235 — JAMAIS os da API NI (full-bridge 350 Ω / 2,5 V),
    que produzem número plausível e errado sem lançar erro (ver CLAUDE.md regra 5).
    Excitação e ponte são fixos do hardware (não vêm da config): expô-los reabriria a
    armadilha do strain. Configuráveis via TOML: gage_factor, poisson, resistência do
    gage e do cabo (3 fios).
    """

    gage_factor: float = 2.15  # meio da faixa 2,14–2,16; varia por lote do extensômetro
    nominal_gage_resistance: float = 120.0
    voltage_excit_val: float = 2.0  # fixo do 9235 (interno)
    bridge_config: str = "QUARTER_BRIDGE_I"  # fixo do 9235
    poisson_ratio: float = 0.3
    lead_wire_resistance: float = 0.0  # 3 fios compensa; ajustar para cabo longo
    min_val: float = -0.001
    max_val: float = 0.001


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
    strain: ParametrosStrain | None = None

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
    strain = _parametros_strain(nome, cfg) if cfg["tipo"] == "strain" else None
    if "pontos" in cfg:
        return _canal_calibrado(nome, cfg, rotulo, strain)
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
        strain=strain,
    )


def _canal_calibrado(nome: str, cfg: dict, rotulo: str | None, strain: "ParametrosStrain | None") -> Canal:
    """Canal com tabela de pontos: regressão linear (default, à la AqDados) ou segmento (opt-in)."""
    metodo = cfg.get("metodo", METODO_PADRAO)
    if metodo not in METODOS_VALIDOS:
        raise ConfiguracaoInvalida(
            f"canal '{nome}': metodo '{metodo}' inválido (use {' ou '.join(METODOS_VALIDOS)})"
        )
    pares = _parsear_pares(nome, cfg["pontos"])
    base = dict(nome=nome, tipo=cfg["tipo"], unidade=cfg["unidade"], rotulo=rotulo, strain=strain)
    if metodo == "segmento":
        return Canal(**base, pontos=_preparar_segmento(nome, pares))
    try:
        return Canal(**base, reta=ajustar_regressao(pares))
    except RegressaoIndeterminada as erro:
        raise ConfiguracaoInvalida(f"canal '{nome}': {erro}") from None


# parâmetros físicos do strain (9235) — só os que variam vêm do TOML; o resto fica no default seguro
_CAMPOS_STRAIN = {
    "gage_factor": "gage_factor",
    "poisson": "poisson_ratio",
    "resistencia": "nominal_gage_resistance",
    "resistencia_cabo": "lead_wire_resistance",
}


def _parametros_strain(nome: str, cfg: dict) -> ParametrosStrain:
    overrides = {
        campo: _numero(nome, chave, cfg[chave])
        for chave, campo in _CAMPOS_STRAIN.items()
        if chave in cfg
    }
    return ParametrosStrain(**overrides)


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
