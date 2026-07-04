from dataclasses import dataclass
from pathlib import Path


class ErroDePerfil(Exception):
    """Base dos erros de gerência de perfis (a biblioteca da tela inicial — ADR-023)."""


class PerfilJaExiste(ErroDePerfil):
    def __init__(self, nome: str):
        super().__init__(f"já existe um ensaio salvo com o nome '{nome}'")
        self.nome = nome


class NomeDePerfilInvalido(ErroDePerfil):
    """Nome de perfil vazio ou com caractere de caminho (`/`, `\\`, `..`)."""


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

    def criar(self, nome: str) -> Perfil:
        nome = _validar_nome(nome)
        self._pasta.mkdir(parents=True, exist_ok=True)  # máquina nova: a pasta pode não existir
        caminho = self._pasta / f"{nome}.toml"
        if caminho.exists():
            raise PerfilJaExiste(nome)
        caminho.write_text("", encoding="utf-8")
        return Perfil(nome=nome, caminho=caminho)


_CARACTERES_DE_CAMINHO = ("/", "\\", "..")


def _validar_nome(nome: str) -> str:
    limpo = nome.strip()
    if not limpo:
        raise NomeDePerfilInvalido("informe um nome para o ensaio")
    if any(sinal in limpo for sinal in _CARACTERES_DE_CAMINHO):
        # o nome vira nome de arquivo: barra path traversal e subpastas
        raise NomeDePerfilInvalido(f"o nome não pode conter '/', '\\' ou '..' (recebido: {nome!r})")
    return limpo
