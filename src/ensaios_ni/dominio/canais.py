import tomllib
from dataclasses import dataclass
from pathlib import Path

from ensaios_ni.dominio.erros import CanalNaoConfigurado, ConfiguracaoInvalida

CAMPOS_OBRIGATORIOS = ("tipo", "unidade", "ganho", "offset")


@dataclass(frozen=True)
class Canal:
    """Canal físico e os coeficientes da sua conversão linear."""

    nome: str
    tipo: str
    unidade: str
    ganho: float
    offset: float


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
    faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in cfg]
    if faltando:
        raise ConfiguracaoInvalida(f"canal '{nome}': campos obrigatórios faltando: {', '.join(faltando)}")
    return Canal(
        nome=nome,
        tipo=cfg["tipo"],
        unidade=cfg["unidade"],
        ganho=_numero(nome, "ganho", cfg["ganho"]),
        offset=_numero(nome, "offset", cfg["offset"]),
    )


def _numero(nome: str, campo: str, valor) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfiguracaoInvalida(f"canal '{nome}': campo '{campo}' deve ser número, recebido {valor!r}")
    return float(valor)
