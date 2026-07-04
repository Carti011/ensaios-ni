"""Launcher do dashboard ligado ao hardware real (NI-DAQmx) — Fase 5.

Diferente da demo (`janela.abrir()`, adaptador `fake`), este entrypoint monta a
`JanelaMonitor` sobre o `AdaptadorDaqmx`, lendo os canais reais do `canais.toml`.
Roda só no Windows (o `nidaqmx` é carregado lazy dentro do adaptador). Repassa
canais + config à janela para que Aferir e os rótulos funcionem no hardware.
"""

import argparse
import tomllib
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ensaios_ni.apresentacao.editor_canais import EditorDeCanais
from ensaios_ni.apresentacao.monitor import MonitorAoVivo
from ensaios_ni.apresentacao.perfis import BibliotecaDePerfis, ErroDePerfil, pasta_padrao
from ensaios_ni.apresentacao.qt.editor_canais import PainelEditorCanais
from ensaios_ni.apresentacao.qt.janela import JanelaMonitor
from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx
from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.dominio.erros import CanalNaoConfigurado, ConfiguracaoInvalida

_ERROS_CONFIG = (FileNotFoundError, ConfiguracaoInvalida, CanalNaoConfigurado, tomllib.TOMLDecodeError)


def montar_janela(
    config: Path,
    taxa_hz: float,
    bloco: int,
    saida: Path,
    capacidade_janela: int | None = None,
) -> JanelaMonitor:
    canais = carregar_canais(config)
    fonte = AdaptadorDaqmx(canais=canais)
    monitor = MonitorAoVivo(
        fonte, canais, taxa_hz, bloco, Path(saida), capacidade_janela=capacidade_janela
    )
    return JanelaMonitor(monitor, canais=canais, caminho_config=Path(config))


class TelaInicial(QWidget):
    """Tela de abertura sem CLI: escolher o canais.toml e entrar no dashboard.

    É o ponto de entrada amigável do programa (o alvo do .exe da Fase 6): o tio clica
    em "Abrir configuração", aponta o arquivo da obra e o dashboard monta com os canais.
    Config inválido vira mensagem na própria tela — nunca traceback.
    """

    def __init__(
        self,
        taxa_hz: float = 1024.0,
        bloco: int = 256,
        saida: Path = Path("ensaio.csv"),
        capacidade_janela: int = 2000,
        pasta_perfis: Path | None = None,
    ):
        super().__init__()
        self._taxa_hz = taxa_hz
        self._bloco = bloco
        self._saida = Path(saida)
        self._capacidade_janela = capacidade_janela
        self._pasta_perfis = Path(pasta_perfis) if pasta_perfis is not None else pasta_padrao()
        self._janela: JanelaMonitor | None = None  # mantém a referência (evita fechar por GC)
        self.setWindowTitle("ensaios-ni")

        self._lista_perfis = QListWidget()
        self._lista_perfis.itemActivated.connect(self._abrir_perfil)
        self._lista_perfis.currentItemChanged.connect(self._sincronizar_botoes)
        self._popular_perfis()

        # ações sobre o ensaio selecionado (habilitam só quando há um perfil escolhido)
        self._btn_editar = QPushButton("Editar canais…")
        self._btn_editar.clicked.connect(self._editar_canais)
        self._btn_renomear = QPushButton("Renomear…")
        self._btn_renomear.clicked.connect(self._renomear)
        self._btn_duplicar = QPushButton("Duplicar")
        self._btn_duplicar.clicked.connect(self._duplicar)
        self._btn_exportar = QPushButton("Exportar…")
        self._btn_exportar.clicked.connect(self._exportar)
        self._btn_remover = QPushButton("Remover")
        self._btn_remover.clicked.connect(self._remover)
        self._acoes_do_selecionado = (
            self._btn_editar, self._btn_renomear, self._btn_duplicar,
            self._btn_exportar, self._btn_remover,
        )
        for botao in self._acoes_do_selecionado:
            botao.setEnabled(False)

        # ações da biblioteca e abertura de arquivo avulso
        self._btn_novo = QPushButton("Novo ensaio…")
        self._btn_novo.clicked.connect(self._novo_ensaio)
        self._btn_importar = QPushButton("Importar…")
        self._btn_importar.clicked.connect(self._importar)
        self._btn_abrir = QPushButton("Abrir configuração…")
        self._btn_abrir.clicked.connect(self._escolher_e_abrir)
        self._lbl_erro = QLabel("")

        do_ensaio = QHBoxLayout()
        for botao in self._acoes_do_selecionado:
            do_ensaio.addWidget(botao)
        do_ensaio.addStretch(1)

        biblioteca = QHBoxLayout()
        for botao in (self._btn_novo, self._btn_importar, self._btn_abrir):
            biblioteca.addWidget(botao)
        biblioteca.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Escolha um ensaio salvo:"))
        layout.addWidget(self._lista_perfis)
        layout.addLayout(do_ensaio)
        layout.addLayout(biblioteca)
        layout.addWidget(self._lbl_erro)

    def abrir_config(self, caminho: Path) -> JanelaMonitor | None:
        try:
            janela = montar_janela(
                caminho, self._taxa_hz, self._bloco, self._saida,
                capacidade_janela=self._capacidade_janela,
            )
        except _ERROS_CONFIG as erro:
            self._lbl_erro.setText(_mensagem_erro(caminho, erro))
            return None
        self._lbl_erro.setText("")
        self._janela = janela
        janela.resize(1000, 600)
        janela.show()
        self.hide()
        return janela

    def _escolher_e_abrir(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir configuração de canais", "", "Config de canais (*.toml)"
        )
        if caminho:
            self.abrir_config(Path(caminho))

    def _popular_perfis(self) -> None:
        self._lista_perfis.clear()
        for perfil in BibliotecaDePerfis(self._pasta_perfis).listar():
            item = QListWidgetItem(perfil.nome)
            item.setData(Qt.ItemDataRole.UserRole, str(perfil.caminho))  # endereço interno; a UI mostra o nome
            self._lista_perfis.addItem(item)

    def _sincronizar_botoes(self, *_) -> None:
        habilitado = self._lista_perfis.currentItem() is not None
        for botao in self._acoes_do_selecionado:
            botao.setEnabled(habilitado)

    def _nome_selecionado(self) -> str | None:
        item = self._lista_perfis.currentItem()
        return item.text() if item is not None else None

    def _abrir_perfil(self, item: QListWidgetItem) -> JanelaMonitor | None:
        return self.abrir_config(Path(item.data(Qt.ItemDataRole.UserRole)))

    def _editar_canais_do_selecionado(self) -> PainelEditorCanais | None:
        item = self._lista_perfis.currentItem()
        if item is None:
            return None
        caminho = Path(item.data(Qt.ItemDataRole.UserRole))
        return PainelEditorCanais(EditorDeCanais(caminho), parent=self)

    def _editar_canais(self) -> None:  # pragma: no cover — abre diálogo modal
        painel = self._editar_canais_do_selecionado()
        if painel is not None:
            painel.exec()

    def _criar_perfil(self, nome: str) -> PainelEditorCanais | None:
        # cria o perfil, atualiza a lista e abre o editor A2 nele; nome inválido/duplicado vira aviso
        try:
            perfil = BibliotecaDePerfis(self._pasta_perfis).criar(nome)
        except ErroDePerfil as erro:
            self._lbl_erro.setText(str(erro))
            return None
        self._lbl_erro.setText("")
        self._popular_perfis()
        self._selecionar_perfil(perfil.nome)
        return PainelEditorCanais(EditorDeCanais(perfil.caminho), parent=self)

    def _selecionar_perfil(self, nome: str) -> None:
        for i in range(self._lista_perfis.count()):
            if self._lista_perfis.item(i).text() == nome:
                self._lista_perfis.setCurrentRow(i)
                return

    def _novo_ensaio(self) -> None:  # pragma: no cover — abre diálogo modal
        nome, ok = QInputDialog.getText(self, "Novo ensaio", "Nome do ensaio (obra):")
        if ok:
            painel = self._criar_perfil(nome)
            if painel is not None:
                painel.exec()

    def _importar_perfil(self, origem: Path):
        # adota um .toml de fora na biblioteca (config inválido/duplicado vira aviso na tela)
        try:
            perfil = BibliotecaDePerfis(self._pasta_perfis).importar(origem)
        except ErroDePerfil as erro:
            self._lbl_erro.setText(str(erro))
            return None
        self._lbl_erro.setText("")
        self._popular_perfis()
        self._selecionar_perfil(perfil.nome)
        return perfil

    def _importar(self) -> None:  # pragma: no cover — abre diálogo modal
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar configuração de canais", "", "Config de canais (*.toml)"
        )
        if caminho:
            self._importar_perfil(Path(caminho))

    def _renomear_perfil(self, atual: str, novo: str):
        try:
            perfil = BibliotecaDePerfis(self._pasta_perfis).renomear(atual, novo)
        except ErroDePerfil as erro:
            self._lbl_erro.setText(str(erro))
            return None
        self._lbl_erro.setText("")
        self._popular_perfis()
        self._selecionar_perfil(perfil.nome)
        return perfil

    def _renomear(self) -> None:  # pragma: no cover — abre diálogo modal
        atual = self._nome_selecionado()
        if atual is None:
            return
        novo, ok = QInputDialog.getText(self, "Renomear ensaio", "Novo nome:", text=atual)
        if ok and novo != atual:
            self._renomear_perfil(atual, novo)

    def _remover_perfil(self, nome: str) -> bool:
        try:
            BibliotecaDePerfis(self._pasta_perfis).remover(nome)
        except ErroDePerfil as erro:
            self._lbl_erro.setText(str(erro))
            return False
        self._lbl_erro.setText("")
        self._popular_perfis()
        return True

    def _remover(self) -> None:  # pragma: no cover — abre diálogo modal
        nome = self._nome_selecionado()
        if nome is None:
            return
        confirma = QMessageBox.question(
            self, "Remover ensaio", f"Remover o ensaio '{nome}'? Esta ação não pode ser desfeita."
        )
        if confirma == QMessageBox.StandardButton.Yes:
            self._remover_perfil(nome)

    def _duplicar_perfil(self, nome: str, novo: str):
        try:
            perfil = BibliotecaDePerfis(self._pasta_perfis).duplicar(nome, novo)
        except ErroDePerfil as erro:
            self._lbl_erro.setText(str(erro))
            return None
        self._lbl_erro.setText("")
        self._popular_perfis()
        self._selecionar_perfil(perfil.nome)
        return perfil

    def _duplicar(self) -> None:  # pragma: no cover — abre diálogo modal
        nome = self._nome_selecionado()
        if nome is None:
            return
        novo, ok = QInputDialog.getText(self, "Duplicar ensaio", "Nome da cópia:", text=f"{nome} cópia")
        if ok:
            self._duplicar_perfil(nome, novo)

    def _exportar_perfil(self, nome: str, destino: Path):
        try:
            caminho = BibliotecaDePerfis(self._pasta_perfis).exportar(nome, destino)
        except ErroDePerfil as erro:
            self._lbl_erro.setText(str(erro))
            return None
        self._lbl_erro.setText("")
        return caminho

    def _exportar(self) -> None:  # pragma: no cover — abre diálogo modal
        nome = self._nome_selecionado()
        if nome is None:
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar configuração", f"{nome}.toml", "Config de canais (*.toml)"
        )
        if caminho:
            self._exportar_perfil(nome, Path(caminho))


def _mensagem_erro(config: Path, erro: Exception) -> str:
    if isinstance(erro, FileNotFoundError):
        return f"config não encontrado: {config}"
    return f"config inválido: {erro}"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ensaios_ni.apresentacao.qt.hardware",
        description="Abre o dashboard ao vivo ligado ao hardware NI (Windows).",
    )
    parser.add_argument("--config", type=Path, default=None,
                        help="canais.toml com os canais reais (sem ele, abre a tela inicial)")
    parser.add_argument("--taxa", type=float, default=1024.0, help="taxa de amostragem em Hz")
    parser.add_argument("--bloco", type=int, default=256, help="amostras por bloco (streaming)")
    parser.add_argument("--saida", type=Path, default=Path("ensaio.csv"),
                        help="CSV onde o ensaio é gravado")
    parser.add_argument("--capacidade-janela", type=int, default=2000,
                        help="pontos exibidos no gráfico (janela deslizante p/ ensaios longos)")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    app, widget = _preparar(argv)
    widget.show()  # pragma: no cover — abre a UI
    app.exec()  # pragma: no cover — bloqueia no event loop


def _preparar(argv=None):
    from PySide6.QtWidgets import QApplication

    # o QApplication precisa existir ANTES de qualquer QWidget (senão o widget aborta)
    app = QApplication.instance() or QApplication([])
    return app, _widget_de(_parse_args(argv))


def _widget_de(args) -> QWidget:
    # sem --config, tela inicial (o tio escolhe o arquivo); com --config, dashboard direto (CLI/dev)
    if args.config is None:
        return TelaInicial(args.taxa, args.bloco, args.saida, args.capacidade_janela)
    try:
        janela = montar_janela(
            args.config, args.taxa, args.bloco, args.saida,
            capacidade_janela=args.capacidade_janela,
        )
    except _ERROS_CONFIG as erro:
        raise SystemExit(_mensagem_erro(args.config, erro)) from None
    janela.resize(1000, 600)
    return janela


if __name__ == "__main__":  # pragma: no cover
    main()
