"""Camada de widget (PySide6) do monitor ao vivo — ADR-015.

Casca fina: liga `QTimer → MonitorAoVivo.passo()` e desenha. Toda a lógica
(estado, conversão, janela, gravação) vive no Presenter, sem PySide. Este é o
único pacote onde `import PySide6` é permitido (ver tests/arquitetura/test_regra_pyside.py).
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ensaios_ni.apresentacao.afericao import Afericao
from ensaios_ni.apresentacao.exportacao import Exportacao
from ensaios_ni.apresentacao.monitor import AquisicaoEmAndamento, EstadoMonitor, MonitorAoVivo
from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.persistencia.config_canais import ler_pontos, salvar_rotulo

if TYPE_CHECKING:
    from ensaios_ni.dominio.canais import Canais

_COR_TRACO = ("#0a9edc", "#e8590c", "#2f9e44", "#9c36b5", "#1864ab", "#c92a2a")
_JANELA_XY = 150  # pontos exibidos no XY: o laço recente, não o histórico todo acumulado


class JanelaMonitor(QWidget):
    """Workspace de painéis: canais à esquerda, gráfico sinal×tempo ao centro, controle no rodapé."""

    def __init__(
        self,
        monitor: MonitorAoVivo,
        canais: "Canais | None" = None,
        caminho_config: Path | None = None,
        intervalo_ms: int = 50,
    ):
        super().__init__()
        self._monitor = monitor
        self._canais = canais
        self._caminho_config = Path(caminho_config) if caminho_config is not None else None
        quadro = monitor.quadro()
        self._nomes = list(quadro.dados)
        self._unidades = quadro.unidades
        # exibição usa o rótulo (Nome do Sinal); sem rótulo, cai no endereço físico
        self._etiquetas = {
            nome: (canais[nome].etiqueta if canais is not None else nome) for nome in self._nomes
        }
        self._visiveis = set(self._nomes)  # seleção de exibição (só afeta o gráfico sinal×tempo)
        self.setWindowTitle("ensaios-ni — monitor ao vivo")

        # painel de canais
        self._tabela = self._montar_tabela()
        self._tabela.itemChanged.connect(self._quando_muda_celula)
        self._btn_aferir = QPushButton("Aferir…")  # abre a aferição do canal selecionado
        self._btn_aferir.setEnabled(self._caminho_config is not None)
        self._btn_aferir.clicked.connect(self._aferir_selecionado)
        # gráfico sinal×tempo (empilhado por unidade)
        self._grafico, self._graficos, self._curvas = self._montar_grafico()
        self._ordem_unidades = list(self._graficos)
        # gráfico XY carga×deformação (ensaio estático)
        self._canal_x = self._nomes[0]
        self._canal_y = self._nomes[-1]
        self._painel_xy = self._montar_xy()
        # barra de controle
        self._btn_iniciar = QPushButton("▶ Iniciar")
        self._btn_parar = QPushButton("■ Parar")
        self._btn_parar.setEnabled(False)
        self._btn_zerar = QPushButton("Zerar")  # tara (Zero Channel): captura o repouso ao vivo
        self._btn_zerar.setEnabled(False)
        self._btn_exportar = QPushButton("Exportar…")  # reusa os exportadores sobre o CSV gravado
        self._btn_exportar.setEnabled(False)
        self._lbl_estado = QLabel()
        self._btn_iniciar.clicked.connect(self.iniciar)
        self._btn_parar.clicked.connect(self.parar)
        self._btn_zerar.clicked.connect(self._monitor.zerar)
        self._btn_exportar.clicked.connect(self._abrir_exportacao)

        # timer de aquisição (não bloqueia a UI)
        self._timer = QTimer(self)
        self._timer.setInterval(intervalo_ms)
        self._timer.timeout.connect(self._ao_passo)

        self._montar_layout()
        self._atualizar_estado()

    def iniciar(self) -> None:
        self._monitor.iniciar()
        self._btn_iniciar.setEnabled(False)
        self._btn_parar.setEnabled(True)
        self._timer.start()
        self._atualizar_estado()

    def parar(self) -> None:
        self._timer.stop()
        self._monitor.parar()
        self._btn_iniciar.setEnabled(True)
        self._btn_parar.setEnabled(False)
        self._atualizar_estado()

    def _ao_passo(self) -> None:
        if not self._monitor.passo():  # esgotou ou erro: o Presenter já encerrou limpo
            self._timer.stop()
            self._btn_iniciar.setEnabled(True)
            self._btn_parar.setEnabled(False)
            self._atualizar_estado()
            return
        quadro = self._monitor.quadro()
        self._desenhar_sinais(quadro)
        self._atualizar_xy()
        self._atualizar_tabela()
        self._atualizar_estado()

    def _desenhar_sinais(self, quadro) -> None:
        # canal oculto pela seleção fica sem traço; gravação e XY não são afetados
        for nome in self._nomes:
            if nome in self._visiveis:
                self._curvas[nome].setData(quadro.tempos, quadro.dados[nome])
            else:
                self._curvas[nome].setData([], [])

    def _esta_visivel(self, nome: str) -> bool:
        return nome in self._visiveis

    def _definir_visivel(self, nome: str, visivel: bool) -> None:
        if visivel:
            self._visiveis.add(nome)
        else:
            self._visiveis.discard(nome)
        self._reorganizar_subplots()
        self._desenhar_sinais(self._monitor.quadro())

    def _unidade_visivel(self, unidade: str) -> bool:
        return any(self._unidades[c] == unidade and c in self._visiveis for c in self._nomes)

    def _subplots_visiveis(self) -> list[str]:
        return [u for u in self._ordem_unidades if self._unidade_visivel(u)]

    def _reorganizar_subplots(self) -> None:
        # recolhe o sub-plot de uma unidade quando todos os seus canais somem da seleção
        self._grafico.clear()
        unidades = self._subplots_visiveis()
        mestre = None
        for linha, unidade in enumerate(unidades):
            plot = self._graficos[unidade]
            self._grafico.addItem(plot, row=linha, col=0)
            plot.setLabel("bottom", "")
            if mestre is None:
                mestre = plot
                plot.setXLink(None)
            else:
                plot.setXLink(mestre)
        if unidades:  # rótulo de tempo só no último visível (eixo X compartilhado)
            self._graficos[unidades[-1]].setLabel("bottom", "tempo", units="s")

    def _quando_muda_celula(self, item) -> None:
        if item.column() != 0:  # só a coluna do sinal tem checkbox/rótulo
            return
        nome = item.data(Qt.ItemDataRole.UserRole)
        if item.text() != self._etiquetas[nome]:  # editou o texto: renomear o sinal
            self._renomear_sinal(nome, item.text())
        else:  # alternou o checkbox: só visibilidade
            self._definir_visivel(nome, item.checkState() == Qt.CheckState.Checked)

    def _renomear_sinal(self, nome: str, rotulo: str) -> None:
        self._etiquetas[nome] = rotulo
        if self._caminho_config is not None:
            salvar_rotulo(self._caminho_config, nome, rotulo)
        for combo in (self._combo_x, self._combo_y):  # reflete o novo rótulo nos seletores X/Y
            indice = combo.findData(nome)
            if indice >= 0:
                combo.setItemText(indice, rotulo)

    def _aferir_selecionado(self) -> None:
        linha = max(self._tabela.currentRow(), 0)
        item = self._tabela.item(linha, 0)
        if item is not None:
            self._abrir_afericao(item.data(Qt.ItemDataRole.UserRole))

    def _abrir_afericao(self, nome: str) -> "PainelAfericao | None":
        # sem arquivo de config carregado não há onde persistir a aferição
        if self._caminho_config is None:
            return None
        afericao = Afericao(
            caminho=self._caminho_config,
            canal=nome,
            pontos=ler_pontos(self._caminho_config, nome),
        )
        painel = PainelAfericao(
            afericao,
            unidade=self._unidades.get(nome, ""),
            titulo_sinal=self._etiquetas[nome],
            parent=self,
        )
        painel.accepted.connect(self._recarregar_calibracao)  # Aplicar relê a calibração no monitor
        painel.show()
        return painel

    def _recarregar_calibracao(self) -> None:
        # aferição persistida no TOML: relê e injeta no monitor (vale do próximo Iniciar)
        if self._caminho_config is None:
            return
        canais = carregar_canais(self._caminho_config)
        try:
            self._monitor.recarregar_canais(canais)
        except AquisicaoEmAndamento:
            return  # iniciou com o painel aberto: já está no TOML, entra no próximo ensaio
        self._canais = canais

    def _abrir_exportacao(self) -> "PainelExportacao | None":
        # exporta o ensaio gravado em disco; sem CSV não há o que exportar
        if not self._monitor.caminho.exists():
            return None
        painel = PainelExportacao(Exportacao(self._monitor.caminho), parent=self)
        painel.show()
        return painel

    def _atualizar_xy(self) -> None:
        par = self._par_xy_atual()
        if par is not None:
            self._curva_xy.setData(par.xs[-_JANELA_XY:], par.ys[-_JANELA_XY:])

    def _par_xy_atual(self):
        if len(self._nomes) < 2:  # XY precisa de dois canais distintos
            return None
        return self._monitor.quadro().par_xy(self._canal_x, self._canal_y)

    def _quando_muda_xy(self) -> None:
        self._canal_x = self._combo_x.currentData()
        self._canal_y = self._combo_y.currentData()
        self._plot_xy.setLabel("bottom", self._unidades.get(self._canal_x, ""))
        self._plot_xy.setLabel("left", self._unidades.get(self._canal_y, ""))
        self._atualizar_xy()

    def _atualizar_tabela(self) -> None:
        for linha, nome in enumerate(self._nomes):
            valor = self._monitor.valor_atual(nome)
            texto = "—" if valor is None else _numero_br(valor)
            self._tabela.setItem(linha, 2, QTableWidgetItem(texto))

    def _atualizar_estado(self) -> None:
        estado = self._monitor.estado
        if estado is EstadoMonitor.ERRO:
            self._lbl_estado.setText(f"● erro: {self._monitor.erro}")
        else:
            self._lbl_estado.setText(f"● {estado.value}")
        # aferir é etapa pré-ensaio: calibração fica fixa durante a aquisição
        self._btn_aferir.setEnabled(
            self._caminho_config is not None and estado is not EstadoMonitor.ADQUIRINDO
        )
        # zerar (tara) captura o repouso ao vivo: só faz sentido adquirindo
        self._btn_zerar.setEnabled(estado is EstadoMonitor.ADQUIRINDO)
        # exportar parte do ensaio gravado NESTA sessão (não de um CSV residual em disco)
        self._btn_exportar.setEnabled(
            estado is not EstadoMonitor.ADQUIRINDO and self._monitor.tem_ensaio
        )

    def _montar_tabela(self) -> QTableWidget:
        tabela = QTableWidget(len(self._nomes), 3)
        tabela.setHorizontalHeaderLabels(["Sinal", "Unidade", "Valor"])
        cabecalho = tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Sinal: cabe o rótulo
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Unidade
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Valor ao vivo
        tabela.verticalHeader().setVisible(False)
        for linha, nome in enumerate(self._nomes):
            # exibe o rótulo (Nome do Sinal); o endereço fica no UserRole (identidade do canal)
            item = QTableWidgetItem(self._etiquetas[nome])
            item.setData(Qt.ItemDataRole.UserRole, nome)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # checkbox de exibição
            item.setCheckState(Qt.CheckState.Checked)
            tabela.setItem(linha, 0, item)
            tabela.setItem(linha, 1, QTableWidgetItem(self._unidades.get(nome, "")))
            tabela.setItem(linha, 2, QTableWidgetItem("—"))
        tabela.setMaximumWidth(360)
        return tabela

    def _montar_grafico(self):
        # empilhamento: um sub-plot por unidade (eixo Y próprio), eixo X de tempo compartilhado
        pg.setConfigOptions(antialias=True, background="w", foreground="k")
        layout = pg.GraphicsLayoutWidget()
        grupos = self._monitor.quadro().agrupar_por_unidade()
        graficos: dict[str, "pg.PlotItem"] = {}
        curvas = {}
        indice_cor = 0
        mestre_x = None
        for linha, grupo in enumerate(grupos):
            plot = layout.addPlot(row=linha, col=0)
            plot.setLabel("left", grupo.unidade)
            plot.showGrid(x=True, y=True, alpha=0.3)
            plot.addLegend()
            if mestre_x is None:
                mestre_x = plot
            else:
                plot.setXLink(mestre_x)
            for nome in grupo.dados:
                cor = _COR_TRACO[indice_cor % len(_COR_TRACO)]
                curvas[nome] = plot.plot([], [], name=nome, pen=pg.mkPen(cor, width=2))
                indice_cor += 1
            graficos[grupo.unidade] = plot
        if grupos:  # rótulo de tempo só no último (eixo X é compartilhado)
            graficos[grupos[-1].unidade].setLabel("bottom", "tempo", units="s")
        return layout, graficos, curvas

    def _montar_xy(self) -> QWidget:
        painel = QWidget()
        coluna = QVBoxLayout(painel)

        seletor = QHBoxLayout()
        self._combo_x = QComboBox()
        self._combo_y = QComboBox()
        for nome in self._nomes:  # exibe o rótulo, guarda o endereço como dado do item
            self._combo_x.addItem(self._etiquetas[nome], nome)
            self._combo_y.addItem(self._etiquetas[nome], nome)
        self._combo_x.setCurrentIndex(self._nomes.index(self._canal_x))
        self._combo_y.setCurrentIndex(self._nomes.index(self._canal_y))
        self._combo_x.currentIndexChanged.connect(self._quando_muda_xy)
        self._combo_y.currentIndexChanged.connect(self._quando_muda_xy)
        seletor.addWidget(QLabel("X"))
        seletor.addWidget(self._combo_x, stretch=1)
        seletor.addWidget(QLabel("Y"))
        seletor.addWidget(self._combo_y, stretch=1)

        self._plot_xy = pg.PlotWidget()
        self._plot_xy.showGrid(x=True, y=True, alpha=0.3)
        self._plot_xy.setLabel("bottom", self._unidades.get(self._canal_x, ""))
        self._plot_xy.setLabel("left", self._unidades.get(self._canal_y, ""))
        self._curva_xy = self._plot_xy.plot([], [], pen=pg.mkPen("#0a9edc", width=2))

        coluna.addLayout(seletor)
        coluna.addWidget(self._plot_xy, stretch=1)
        return painel

    def _estilizar_divisor(self, splitter: QSplitter) -> None:
        # alça visível entre os gráficos: barra-pílula sutil que acende no acento ao passar o mouse
        splitter.setHandleWidth(10)
        splitter.setStyleSheet(
            "QSplitter::handle:horizontal {"
            "  background: rgba(128, 128, 128, 0.30);"
            "  margin: 12px 3px;"
            "  border-radius: 2px;"
            "}"
            f"QSplitter::handle:horizontal:hover {{ background: {_COR_TRACO[0]}; }}"
        )

    def _montar_layout(self) -> None:
        graficos = QSplitter(Qt.Orientation.Horizontal)
        graficos.addWidget(self._grafico)
        graficos.addWidget(self._painel_xy)
        graficos.setStretchFactor(0, 3)
        graficos.setStretchFactor(1, 2)
        self._estilizar_divisor(graficos)
        self._splitter = graficos

        painel_canais = QVBoxLayout()
        painel_canais.addWidget(self._tabela)
        painel_canais.addWidget(self._btn_aferir)

        topo = QHBoxLayout()
        topo.addLayout(painel_canais)
        topo.addWidget(graficos, stretch=1)

        rodape = QHBoxLayout()
        rodape.addWidget(self._btn_iniciar)
        rodape.addWidget(self._btn_parar)
        rodape.addWidget(self._btn_zerar)
        rodape.addWidget(self._btn_exportar)
        rodape.addStretch(1)
        rodape.addWidget(self._lbl_estado)

        raiz = QVBoxLayout(self)
        raiz.addLayout(topo, stretch=1)
        raiz.addLayout(rodape)


class PainelAfericao(QDialog):
    """Aferição por regressão linear de um canal, à la AqDados (Fase 4, fatia 3 — ADR-015/006).

    Casca fina sobre o Presenter `Afericao`: tabela de pontos `(V, valor eng.)` editável, ganho da
    reta e correlação ao vivo, e Aplicar persiste a calibração no TOML. Decimal vírgula (BR).
    """

    def __init__(
        self,
        afericao: Afericao,
        unidade: str = "",
        titulo_sinal: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._afericao = afericao
        self._unidade = unidade
        self.setWindowTitle(f"Aferição — {titulo_sinal}")
        self.setMinimumWidth(380)

        self._tabela = QTableWidget(0, 2)
        self._tabela.setHorizontalHeaderLabels(["Tensão (V)", f"Valor ({unidade})"])
        self._tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabela.itemChanged.connect(self._sincronizar)

        # ganho K (V/un) e 1/K (un/V) como o AqDados mostra (ver referencia-lynx §1.3)
        self._lbl_ganho_k = QLabel()
        self._lbl_ganho_1k = QLabel()
        self._lbl_correlacao = QLabel()
        btn_inserir = QPushButton("Inserir ponto")
        btn_remover = QPushButton("Remover ponto")
        btn_inserir.clicked.connect(self._inserir_linha_vazia)
        btn_remover.clicked.connect(self._remover_selecionada)
        # botões com texto próprio (os StandardButton do Qt vêm em inglês — português total)
        self._botoes = QDialogButtonBox()
        self._btn_aplicar = self._botoes.addButton("Aplicar", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancelar = self._botoes.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        self._btn_aplicar.clicked.connect(self._aplicar)
        btn_cancelar.clicked.connect(self.reject)

        self._preencher(afericao.pontos)
        self._montar_layout(btn_inserir, btn_remover)
        self._sincronizar()

    def _preencher(self, pontos) -> None:
        self._tabela.blockSignals(True)
        self._tabela.setRowCount(0)
        for volts, valor in pontos:
            self._anexar_linha(volts, valor)
        self._tabela.blockSignals(False)

    def _anexar_linha(self, volts: float | None = None, valor: float | None = None) -> None:
        linha = self._tabela.rowCount()
        self._tabela.insertRow(linha)
        self._tabela.setItem(linha, 0, QTableWidgetItem("" if volts is None else _numero_br(volts)))
        self._tabela.setItem(linha, 1, QTableWidgetItem("" if valor is None else _numero_br(valor)))

    def _inserir_linha_vazia(self) -> None:
        self._anexar_linha()

    def _remover_selecionada(self) -> None:
        linha = self._tabela.currentRow()
        if linha >= 0:
            self._tabela.removeRow(linha)
            self._sincronizar()

    def _ler_tabela(self) -> list[tuple[float, float]]:
        pontos = []
        for linha in range(self._tabela.rowCount()):
            volts = _parse_br(self._tabela.item(linha, 0))
            valor = _parse_br(self._tabela.item(linha, 1))
            if volts is not None and valor is not None:
                pontos.append((volts, valor))
        return pontos

    def _sincronizar(self, *_) -> None:
        self._afericao.definir_pontos(self._ler_tabela())
        reta = self._afericao.reta()
        unidade = self._unidade
        ganho_k = self._afericao.ganho_inverso()
        self._lbl_ganho_k.setText(
            "Ganho K: —" if ganho_k is None else f"Ganho K: {_numero_br(ganho_k)} V/{unidade}"
        )
        self._lbl_ganho_1k.setText(
            "Ganho 1/K: —" if reta is None else f"Ganho 1/K: {_numero_br(reta.a)} {unidade}/V"
        )
        self._lbl_correlacao.setText(f"correlação: {self._afericao.correlacao_percentual()}")
        self._btn_aplicar.setEnabled(reta is not None)

    def _aplicar(self) -> None:
        self._afericao.aplicar()
        self.accept()

    def _montar_layout(self, btn_inserir: QPushButton, btn_remover: QPushButton) -> None:
        acoes = QHBoxLayout()
        acoes.addWidget(btn_inserir)
        acoes.addWidget(btn_remover)
        acoes.addStretch(1)
        ganhos = QHBoxLayout()
        ganhos.addWidget(self._lbl_ganho_k)
        ganhos.addStretch(1)
        ganhos.addWidget(self._lbl_ganho_1k)
        indicadores = QVBoxLayout()
        indicadores.addLayout(ganhos)
        indicadores.addWidget(self._lbl_correlacao)
        raiz = QVBoxLayout(self)
        raiz.addWidget(self._tabela)
        raiz.addLayout(acoes)
        raiz.addLayout(indicadores)
        raiz.addWidget(self._botoes)


class PainelExportacao(QDialog):
    """Exporta o ensaio gravado para outro formato (Fase 4, fatia 4 — ADR-011/012).

    Casca fina sobre o Presenter `Exportacao`: escolhe formato, sinais e janela de tempo;
    Exportar abre o seletor de arquivo. Reusa os exportadores prontos (não há lógica nova).
    """

    def __init__(self, exportacao: Exportacao, parent: QWidget | None = None):
        super().__init__(parent)
        self._exportacao = exportacao
        self.setWindowTitle("Exportar ensaio")
        self.setMinimumWidth(360)

        self._combo_formato = QComboBox()
        self._combo_formato.addItems(exportacao.formatos)

        self._lista_sinais = QListWidget()
        for sinal in exportacao.sinais():  # à la AqDados: escolhe quais sinais exportar
            item = QListWidgetItem(sinal)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self._lista_sinais.addItem(item)

        self._inicio = QLineEdit()
        self._inicio.setPlaceholderText("início (s)")
        self._fim = QLineEdit()
        self._fim.setPlaceholderText("fim (s)")

        self._botoes = QDialogButtonBox()  # texto próprio: português total
        btn_exportar = self._botoes.addButton("Exportar", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancelar = self._botoes.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        btn_exportar.clicked.connect(self._escolher_destino_e_exportar)
        btn_cancelar.clicked.connect(self.reject)

        self._montar_layout()

    def _sinais_escolhidos(self) -> list[str] | None:
        marcados = [
            self._lista_sinais.item(i).text()
            for i in range(self._lista_sinais.count())
            if self._lista_sinais.item(i).checkState() == Qt.CheckState.Checked
        ]
        return None if len(marcados) == self._lista_sinais.count() else marcados  # todos = None

    def _escolher_destino_e_exportar(self) -> None:
        destino, _ = QFileDialog.getSaveFileName(
            self, "Salvar exportação", _sugestao_nome(self._combo_formato.currentText())
        )
        if destino:
            self.exportar_para(Path(destino))
            self.accept()

    def exportar_para(self, destino: Path) -> None:
        self._exportacao.exportar(
            self._combo_formato.currentText(),
            destino,
            sinais=self._sinais_escolhidos(),
            inicio_s=_parse_br(self._inicio),
            fim_s=_parse_br(self._fim),
        )

    def _montar_layout(self) -> None:
        janela = QHBoxLayout()
        janela.addWidget(QLabel("Janela:"))
        janela.addWidget(self._inicio)
        janela.addWidget(QLabel("a"))
        janela.addWidget(self._fim)
        raiz = QVBoxLayout(self)
        raiz.addWidget(QLabel("Formato"))
        raiz.addWidget(self._combo_formato)
        raiz.addWidget(QLabel("Sinais"))
        raiz.addWidget(self._lista_sinais)
        raiz.addLayout(janela)
        raiz.addWidget(self._botoes)


def _sugestao_nome(formato: str) -> str:
    extensao = {"csv-excel-br": ".csv", "xlsx": ".xlsx", "txt-aqanalysis": ".txt"}
    return f"ensaio{extensao.get(formato, '.csv')}"


def _parse_br(item) -> float | None:
    if item is None:
        return None
    try:
        return float(item.text().strip().replace(",", "."))
    except ValueError:
        return None


def _numero_br(valor: float) -> str:
    return f"{valor:.4f}".replace(".", ",")


def _demonstracao():
    """Monta a demo do Mac (fake + sinal sintético) e um canais.toml de trabalho editável.

    A UI escreve a aferição numa CÓPIA do exemplo (o versionado não é tocado), para o Aferir
    funcionar de ponta a ponta no Mac.
    """
    import shutil
    import tempfile

    from ensaios_ni.aplicacao.demo import _CONFIG_EXEMPLO, _sinais_sinteticos
    from ensaios_ni.aquisicao.fake import AquisicaoFake
    from ensaios_ni.dominio.canais import carregar_canais

    tmp = Path(tempfile.gettempdir())
    config_trabalho = tmp / "ensaios-ni-canais.toml"
    shutil.copy(_CONFIG_EXEMPLO, config_trabalho)

    taxa_hz = 100.0
    canais = carregar_canais(config_trabalho)
    tensoes, strains = _sinais_sinteticos(canais, amostras=5000, taxa_hz=taxa_hz)
    fonte = AquisicaoFake(tensoes=tensoes, strains=strains)
    monitor = MonitorAoVivo(
        fonte, canais, taxa_hz, amostras_por_bloco=20,
        caminho=tmp / "ensaio-dashboard.csv", capacidade_janela=500,
    )
    return monitor, canais, config_trabalho


def abrir(monitor: MonitorAoVivo | None = None) -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    if monitor is None:
        monitor, canais, config = _demonstracao()
        janela = JanelaMonitor(monitor, canais=canais, caminho_config=config)
    else:
        janela = JanelaMonitor(monitor)
    janela.resize(1000, 600)
    janela.show()
    app.exec()


if __name__ == "__main__":
    abrir()
