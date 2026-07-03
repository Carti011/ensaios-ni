from dataclasses import dataclass
from pathlib import Path


def pasta_padrao() -> Path:
    """Onde o app guarda os perfis do tio — uma pasta no home, sem depender do locale do SO
    ("Documents" vs "Documentos"). O tio nunca precisa navegar até aqui."""
    return Path.home() / "ensaios-ni"


@dataclass(frozen=True)
class Perfil:
    """Uma configuração de canais salva, identificada por um nome amigável (a obra/ensaio).

    O `nome` é o nome do arquivo sem extensão — o que o tio reconhece; o `caminho` é o `.toml`
    que o dashboard abre. Ver [ADR-023].
    """

    nome: str
    caminho: Path


class BibliotecaDePerfis:
    """Presenter da biblioteca de perfis (Fase 6, fatia A1 — ADR-023).

    Lista as configurações de canais de uma pasta como perfis, para a tela inicial exibir e o tio
    escolher por nome, sem abrir arquivo. Python puro, sem PySide — testável no Mac sem display.
    """

    def __init__(self, pasta: Path) -> None:
        self._pasta = Path(pasta)

    def listar(self) -> list[Perfil]:
        # o .meta.toml (metadata de ensaio, ADR-018) também casa com *.toml, mas não é um perfil
        arquivos = (a for a in self._pasta.glob("*.toml") if not a.name.endswith(".meta.toml"))
        return [Perfil(nome=a.stem, caminho=a) for a in sorted(arquivos, key=lambda a: a.stem)]
