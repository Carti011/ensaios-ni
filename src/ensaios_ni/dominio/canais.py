import tomllib
from dataclasses import dataclass
from pathlib import Path

from ensaios_ni.dominio.erros import CanalNaoConfigurado, ConfiguracaoInvalida

CAMPOS_BASE = ("tipo", "unidade")
TIPOS_VALIDOS = ("tensao", "strain")


@dataclass(frozen=True)
class Canal:
    """Canal físico e sua conversão: por pontos de calibração ou linear (ganho/offset)."""

    nome: str
    tipo: str
    unidade: str
    ganho: float | None = None
    offset: float | None = None
    pontos: tuple[tuple[float, float], ...] | None = None


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
    if "pontos" in cfg:
        return Canal(
            nome=nome,
            tipo=cfg["tipo"],
            unidade=cfg["unidade"],
            pontos=_pontos(nome, cfg["pontos"]),
        )
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
        ganho=_numero(nome, "ganho", cfg["ganho"]),
        offset=_numero(nome, "offset", cfg["offset"]),
    )


def _pontos(nome: str, valor) -> tuple[tuple[float, float], ...]:
    if not isinstance(valor, list) or len(valor) < 2:
        raise ConfiguracaoInvalida(f"canal '{nome}': 'pontos' precisa de ao menos 2 pares [volts, valor]")
    pares = []
    for item in valor:
        if not isinstance(item, list) or len(item) != 2:
            raise ConfiguracaoInvalida(f"canal '{nome}': cada ponto deve ser um par [volts, valor], recebido {item!r}")
        pares.append((_numero(nome, "pontos", item[0]), _numero(nome, "pontos", item[1])))
    pares.sort(key=lambda par: par[0])
    if len({volts for volts, _ in pares}) != len(pares):
        raise ConfiguracaoInvalida(f"canal '{nome}': há pontos com o mesmo valor de volts (curva ambígua)")
    return tuple(pares)


def _numero(nome: str, campo: str, valor) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfiguracaoInvalida(f"canal '{nome}': campo '{campo}' deve ser número, recebido {valor!r}")
    return float(valor)
