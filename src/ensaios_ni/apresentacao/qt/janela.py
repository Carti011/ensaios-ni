"""Camada de widget (PySide6) do monitor ao vivo — ADR-015.

Casca fina: liga `QTimer → MonitorAoVivo.passo()` e desenha. Toda a lógica
(estado, conversão, janela, gravação) vive no Presenter, sem PySide. Este é o
único pacote onde `import PySide6` é permitido (ver tests/arquitetura/test_regra_pyside.py).
"""

from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ensaios_ni.apresentacao.monitor import EstadoMonitor, MonitorAoVivo

_COR_TRACO = ("#0a9edc", "#e8590c", "#2f9e44", "#9c36b5", "#1864ab", "#c92a2a")


class JanelaMonitor(QWidget):
    """Workspace de painéis: canais à esquerda, gráfico sinal×tempo ao centro, controle no rodapé."""

    def __init__(self, monitor: MonitorAoVivo, intervalo_ms: int = 50):
        super().__init__()
        self._monitor = monitor
        quadro = monitor.quadro()
        self._nomes = list(quadro.dados)
        self._unidades = quadro.unidades
        self.setWindowTitle("ensaios-ni — monitor ao vivo")

        # painel de canais
        self._tabela = self._montar_tabela()
        # gráfico
        self._grafico, self._curvas = self._montar_grafico()
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
        for nome in self._nomes:
            self._curvas[nome].setData(quadro.tempos, quadro.dados[nome])
        self._atualizar_tabela()
        self._atualizar_estado()

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
            tabela.setItem(linha, 0, QTableWidgetItem(nome))
            tabela.setItem(linha, 1, QTableWidgetItem(self._unidades.get(nome, "")))
            tabela.setItem(linha, 2, QTableWidgetItem("—"))
        tabela.setMaximumWidth(320)
        return tabela

    def _montar_grafico(self):
        pg.setConfigOptions(antialias=True, background="w", foreground="k")
        grafico = pg.PlotWidget()
        grafico.setLabel("bottom", "tempo", units="s")
        grafico.addLegend()
        grafico.showGrid(x=True, y=True, alpha=0.3)
        curvas = {}
        for indice, nome in enumerate(self._nomes):
            cor = _COR_TRACO[indice % len(_COR_TRACO)]
            curvas[nome] = grafico.plot([], [], name=nome, pen=pg.mkPen(cor, width=2))
        return grafico, curvas

    def _montar_layout(self) -> None:
        topo = QHBoxLayout()
        topo.addWidget(self._tabela)
        topo.addWidget(self._grafico, stretch=1)

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
