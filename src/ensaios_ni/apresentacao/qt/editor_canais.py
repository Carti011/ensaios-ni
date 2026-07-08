from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ensaios_ni.apresentacao.editor_canais import EditorDeCanais
from ensaios_ni.dominio.erros import ConfiguracaoInvalida


def _texto_num(valor: float | None) -> str:
    # exibição em decimal vírgula (BR) — o que o tio lê; o parse (_num) aceita vírgula e ponto
    return "" if valor is None else str(valor).replace(".", ",")


def _num(texto: str) -> float | None:
    # aceita vírgula (BR) ou ponto; vazio/ inválido -> None (campo opcional)
    texto = texto.strip().replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


class PainelEditorCanais(QDialog):
    """Editor da tabela de canais de um perfil (Fase 6, fatia A2 — ADR-023).

    Casca fina sobre o Presenter `EditorDeCanais`: lista os canais, adiciona/edita por
    diálogo-formulário e remove. Cada operação persiste na hora no `.toml` do perfil.
    """

    def __init__(self, editor: EditorDeCanais, parent: QWidget | None = None):
        super().__init__(parent)
        self._editor = editor
        self.setWindowTitle("Canais do ensaio")
        self.setMinimumWidth(420)

        self._tabela = QTableWidget(0, 3)
        self._tabela.setHorizontalHeaderLabels(["Sinal", "Tipo", "Unidade"])
        self._tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._recarregar()

        btn_adicionar = QPushButton("Adicionar…")
        btn_editar = QPushButton("Editar…")
        btn_remover = QPushButton("Remover")
        btn_adicionar.clicked.connect(self._adicionar)
        btn_editar.clicked.connect(self._editar)
        btn_remover.clicked.connect(self._remover_selecionado)

        acoes = QHBoxLayout()
        acoes.addWidget(btn_adicionar)
        acoes.addWidget(btn_editar)
        acoes.addWidget(btn_remover)
        acoes.addStretch(1)

        raiz = QVBoxLayout(self)
        raiz.addWidget(self._tabela)
        raiz.addLayout(acoes)

    def _recarregar(self) -> None:
        # listagem TOLERANTE (linhas, não canais): o editor abre mesmo com um canal inválido no
        # perfil, pra o tio poder removê-lo — antes, um canal incompleto derrubava o app ao abrir.
        self._tabela.setRowCount(0)
        for canal in self._editor.linhas():
            linha = self._tabela.rowCount()
            self._tabela.insertRow(linha)
            sinal = QTableWidgetItem(canal.etiqueta)
            sinal.setData(Qt.ItemDataRole.UserRole, canal.nome)  # endereço interno; a UI mostra a etiqueta
            self._tabela.setItem(linha, 0, sinal)
            self._tabela.setItem(linha, 1, QTableWidgetItem(canal.tipo))
            self._tabela.setItem(linha, 2, QTableWidgetItem(canal.unidade))

    def _remover_selecionado(self) -> None:
        linha = self._tabela.currentRow()
        if linha < 0:
            return
        nome = self._tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        self._editor.remover_canal(nome)
        self._recarregar()

    def _aplicar_canal(self, nome: str, campos: dict) -> None:
        self._editor.adicionar_canal(nome, campos)
        self._recarregar()

    def _tentar_aplicar(self, nome: str, campos: dict) -> None:  # pragma: no cover — aviso modal
        # o Presenter valida o essencial (tipo/unidade); mostra o motivo em vez de falhar mudo
        try:
            self._aplicar_canal(nome, campos)
        except ConfiguracaoInvalida as erro:
            QMessageBox.warning(self, "Canal inválido", str(erro))

    def _adicionar(self) -> None:  # pragma: no cover — abre diálogo modal
        dialogo = DialogoCanal(parent=self)
        if dialogo.exec():
            nome, campos = dialogo.campos()
            if nome:
                self._tentar_aplicar(nome, campos)

    def _editar(self) -> None:  # pragma: no cover — abre diálogo modal
        linha = self._tabela.currentRow()
        if linha < 0:
            return
        nome = self._tabela.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        dialogo = DialogoCanal(nome, self._editor.campos(nome), parent=self)  # campos crus: reabre até canal inválido
        if dialogo.exec():
            novo_nome, campos = dialogo.campos()
            if not novo_nome:
                return
            if novo_nome != nome:
                self._editor.remover_canal(nome)  # endereço mudou: remove o antigo
            self._tentar_aplicar(novo_nome, campos)


class DialogoCanal(QDialog):
    """Formulário de um canal (endereço, Nome do Sinal, tipo, unidade, conversão) — ADR-023 fatia A2.

    Editar substitui o canal pelo que está aqui (decisão do Weslley): a calibração por pontos, se
    houver, é zerada — o tio re-afere pelo Aferir. Decimal aceita vírgula ou ponto.
    """

    def __init__(self, nome: str = "", campos: dict | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        campos = campos or {}
        self.setWindowTitle("Canal")
        self.setMinimumWidth(360)

        self._endereco = QLineEdit(nome)
        self._rotulo = QLineEdit(campos.get("rotulo", ""))
        self._tipo = QComboBox()
        self._tipo.addItems(["tensao", "strain"])
        if campos.get("tipo"):
            self._tipo.setCurrentText(campos["tipo"])
        self._unidade = QLineEdit(campos.get("unidade", ""))
        self._ganho = QLineEdit(_texto_num(campos.get("ganho")))
        self._offset = QLineEdit(_texto_num(campos.get("offset")))
        self._gage_factor = QLineEdit(_texto_num(campos.get("gage_factor")))

        form = QFormLayout()
        form.addRow("Endereço (NI-MAX)", self._endereco)
        form.addRow("Nome do Sinal", self._rotulo)
        form.addRow("Tipo", self._tipo)
        form.addRow("Unidade", self._unidade)
        form.addRow("Ganho", self._ganho)
        form.addRow("Offset", self._offset)
        form.addRow("Gage factor (strain)", self._gage_factor)

        botoes = QDialogButtonBox()
        self._aplicar = botoes.addButton("Aplicar", QDialogButtonBox.ButtonRole.AcceptRole)
        cancelar = botoes.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        self._aplicar.clicked.connect(self.accept)
        cancelar.clicked.connect(self.reject)
        # validação inline: Aplicar só habilita com endereço + unidade (sem aviso pós-clique)
        self._endereco.textChanged.connect(self._sincronizar)
        self._unidade.textChanged.connect(self._sincronizar)

        raiz = QVBoxLayout(self)
        raiz.addLayout(form)
        raiz.addWidget(botoes)
        self._sincronizar()

    def _sincronizar(self) -> None:
        valido = bool(self._endereco.text().strip()) and bool(self._unidade.text().strip())
        self._aplicar.setEnabled(valido)

    def campos(self) -> tuple[str, dict]:
        nome = self._endereco.text().strip()
        dados: dict = {"tipo": self._tipo.currentText(), "unidade": self._unidade.text().strip()}
        rotulo = self._rotulo.text().strip()
        if rotulo:
            dados["rotulo"] = rotulo
        for chave, widget in (("ganho", self._ganho), ("offset", self._offset)):
            valor = _num(widget.text())
            if valor is not None:
                dados[chave] = valor
        if dados["tipo"] == "strain":
            gage = _num(self._gage_factor.text())
            if gage is not None:
                dados["gage_factor"] = gage
        return nome, dados
