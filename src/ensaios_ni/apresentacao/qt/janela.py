"""Camada de widget (PySide6) do monitor ao vivo — ADR-015.

Casca fina: liga `QTimer → MonitorAoVivo.passo()` e desenha. Toda a lógica
(estado, conversão, janela, gravação) vive no Presenter, sem PySide. Este é o
único pacote onde `import PySide6` é permitido (ver tests/arquitetura/test_regra_pyside.py).
"""

from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ensaios_ni.apresentacao.monitor import EstadoMonitor, MonitorAoVivo

_COR_TRACO = ("#0a9edc", "#e8590c", "#2f9e44", "#9c36b5", "#1864ab", "#c92a2a")
_JANELA_XY = 150  # pontos exibidos no XY: o laço recente, não o histórico todo acumulado


class JanelaMonitor(QWidget):
    """Workspace de painéis: canais à esquerda, gráfico sinal×tempo ao centro, controle no rodapé."""

    def __init__(self, monitor: MonitorAoVivo, intervalo_ms: int = 50):
        super().__init__()
        self._monitor = monitor
        quadro = monitor.quadro()
        self._nomes = list(quadro.dados)
        self._unidades = quadro.unidades
        self._visiveis = set(self._nomes)  # seleção de exibição (só afeta o gráfico sinal×tempo)
        self.setWindowTitle("ensaios-ni — monitor ao vivo")

        # painel de canais
        self._tabela = self._montar_tabela()
        self._tabela.itemChanged.connect(self._quando_muda_celula)
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
        self._lbl_estado = QLabel()
        self._btn_iniciar.clicked.connect(self.iniciar)
        self._btn_parar.clicked.connect(self.parar)

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
        if item.column() != 0:  # só a coluna do canal tem checkbox
            return
        self._definir_visivel(item.text(), item.checkState() == Qt.CheckState.Checked)

    def _atualizar_xy(self) -> None:
        par = self._par_xy_atual()
        if par is not None:
            self._curva_xy.setData(par.xs[-_JANELA_XY:], par.ys[-_JANELA_XY:])

    def _par_xy_atual(self):
        if len(self._nomes) < 2:  # XY precisa de dois canais distintos
            return None
        return self._monitor.quadro().par_xy(self._canal_x, self._canal_y)

    def _quando_muda_xy(self) -> None:
        self._canal_x = self._combo_x.currentText()
        self._canal_y = self._combo_y.currentText()
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

    def _montar_tabela(self) -> QTableWidget:
        tabela = QTableWidget(len(self._nomes), 3)
        tabela.setHorizontalHeaderLabels(["Canal", "Unidade", "Valor"])
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabela.verticalHeader().setVisible(False)
        for linha, nome in enumerate(self._nomes):
            item = QTableWidgetItem(nome)  # checkbox liga/desliga a exibição do canal (à la AqDados)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            tabela.setItem(linha, 0, item)
            tabela.setItem(linha, 1, QTableWidgetItem(self._unidades.get(nome, "")))
            tabela.setItem(linha, 2, QTableWidgetItem("—"))
        tabela.setMaximumWidth(320)
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
        self._combo_x.addItems(self._nomes)
        self._combo_y.addItems(self._nomes)
        self._combo_x.setCurrentText(self._canal_x)
        self._combo_y.setCurrentText(self._canal_y)
        self._combo_x.currentTextChanged.connect(self._quando_muda_xy)
        self._combo_y.currentTextChanged.connect(self._quando_muda_xy)
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

    def _montar_layout(self) -> None:
        graficos = QSplitter(Qt.Orientation.Horizontal)
        graficos.addWidget(self._grafico)
        graficos.addWidget(self._painel_xy)
        graficos.setStretchFactor(0, 3)
        graficos.setStretchFactor(1, 2)

        topo = QHBoxLayout()
        topo.addWidget(self._tabela)
        topo.addWidget(graficos, stretch=1)

        rodape = QHBoxLayout()
        rodape.addWidget(self._btn_iniciar)
        rodape.addWidget(self._btn_parar)
        rodape.addStretch(1)
        rodape.addWidget(self._lbl_estado)

        raiz = QVBoxLayout(self)
        raiz.addLayout(topo, stretch=1)
        raiz.addLayout(rodape)


def _numero_br(valor: float) -> str:
    return f"{valor:.4f}".replace(".", ",")


def _monitor_demonstracao() -> MonitorAoVivo:
    """Monta um monitor com o adaptador fake e sinal sintético, para rodar no Mac."""
    import tempfile

    from ensaios_ni.aplicacao.demo import _CONFIG_EXEMPLO, _sinais_sinteticos
    from ensaios_ni.aquisicao.fake import AquisicaoFake
    from ensaios_ni.dominio.canais import carregar_canais

    taxa_hz = 100.0
    canais = carregar_canais(_CONFIG_EXEMPLO)
    tensoes, strains = _sinais_sinteticos(canais, amostras=5000, taxa_hz=taxa_hz)
    fonte = AquisicaoFake(tensoes=tensoes, strains=strains)
    saida = Path(tempfile.gettempdir()) / "ensaio-dashboard.csv"
    return MonitorAoVivo(
        fonte, canais, taxa_hz, amostras_por_bloco=20, caminho=saida, capacidade_janela=500
    )


def abrir(monitor: MonitorAoVivo | None = None) -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    janela = JanelaMonitor(monitor or _monitor_demonstracao())
    janela.resize(1000, 600)
    janela.show()
    app.exec()


if __name__ == "__main__":
    abrir()
