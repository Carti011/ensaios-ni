from pathlib import Path
from typing import Any

from ensaios_ni.dominio.canais import TIPOS_VALIDOS, Canais, carregar_canais
from ensaios_ni.dominio.erros import ConfiguracaoInvalida
from ensaios_ni.persistencia import config_canais


class EditorDeCanais:
    """Presenter do editor de canais de um perfil (Fase 6, fatia A2 — ADR-023).

    O tio monta a tabela de canais pela tela (à la AqDados) sem editar o `.toml` à mão. Cada operação
    persiste na hora no arquivo do perfil. Python puro, sem PySide — testável no Mac sem display.
    """

    def __init__(self, caminho: Path) -> None:
        self._caminho = Path(caminho)

    def canais(self) -> Canais:
        return carregar_canais(self._caminho)

    def adicionar_canal(self, nome: str, campos: dict[str, Any]) -> None:
        # antecipa o aviso essencial (ADR-023 dec. 4); o carregar_canais é a rede de segurança final
        self._validar_essencial(nome, campos)
        config_canais.salvar_canal(self._caminho, nome, campos)

    def remover_canal(self, nome: str) -> None:
        config_canais.remover_canal(self._caminho, nome)

    @staticmethod
    def _validar_essencial(nome: str, campos: dict[str, Any]) -> None:
        tipo = campos.get("tipo")
        if tipo not in TIPOS_VALIDOS:
            raise ConfiguracaoInvalida(
                f"canal '{nome}': tipo '{tipo}' inválido (use {' ou '.join(TIPOS_VALIDOS)})"
            )
        if not campos.get("unidade"):
            raise ConfiguracaoInvalida(f"canal '{nome}': informe a unidade")
