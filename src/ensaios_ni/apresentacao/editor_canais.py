import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ensaios_ni.dominio.canais import TIPOS_VALIDOS, Canais, carregar_canais, validar_canal
from ensaios_ni.dominio.erros import ConfiguracaoInvalida
from ensaios_ni.persistencia import config_canais


@dataclass(frozen=True)
class LinhaCanal:
    """Um canal para exibição no editor (nome, tipo, unidade), sem validar a conversão.

    Diferente do `Canal` (que exige config válida), serve à listagem tolerante: o editor
    precisa mostrar até um canal incompleto para o tio poder corrigi-lo ou removê-lo.
    """

    nome: str
    tipo: str
    unidade: str
    rotulo: str | None = None

    @property
    def etiqueta(self) -> str:
        return self.rotulo or self.nome


class EditorDeCanais:
    """Presenter do editor de canais de um perfil (Fase 6, fatia A2 — ADR-023).

    O tio monta a tabela de canais pela tela (à la AqDados) sem editar o `.toml` à mão. Cada operação
    persiste na hora no arquivo do perfil. Python puro, sem PySide — testável no Mac sem display.
    """

    def __init__(self, caminho: Path) -> None:
        self._caminho = Path(caminho)

    def canais(self) -> Canais:
        return carregar_canais(self._caminho)

    def linhas(self) -> list[LinhaCanal]:
        """Canais do perfil para exibição, TOLERANTE a config inválida.

        Lê os campos crus do TOML sem exigir conversão válida — assim o editor abre e lista
        mesmo um perfil com canal incompleto (o cenário que antes travava o app), deixando o
        tio removê-lo. A validação séria segue no `canais()`/`carregar_canais`.
        """
        return [
            LinhaCanal(
                nome=nome,
                tipo=str(cfg.get("tipo", "")),
                unidade=str(cfg.get("unidade", "")),
                rotulo=cfg.get("rotulo"),
            )
            for nome, cfg in self._canais_crus().items()
        ]

    def campos(self, nome: str) -> dict[str, Any]:
        """Campos crus de um canal, para reabrir no formulário — TOLERANTE a config inválida.

        Não passa pelo `canais()` (que valida o perfil todo): assim dá para reeditar um canal
        mesmo que outro canal do perfil esteja quebrado — inclusive o próprio canal inválido.
        """
        return dict(self._canais_crus().get(nome, {}))

    def _canais_crus(self) -> dict[str, dict]:
        return tomllib.loads(Path(self._caminho).read_text(encoding="utf-8")).get("canais", {})

    def adicionar_canal(self, nome: str, campos: dict[str, Any]) -> None:
        # valida pela MESMA regra do carregar_canais ANTES de gravar (ADR-023 dec. 4): recusa um
        # canal que a releitura rejeitaria — senão o perfil fica num estado que trava o editor.
        self._validar_essencial(nome, campos)  # unidade não-vazia (o domínio não checa) — melhor aviso
        validar_canal(nome, campos)  # regra completa: exige conversão (ganho/offset ou pontos), tipo, etc.
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
