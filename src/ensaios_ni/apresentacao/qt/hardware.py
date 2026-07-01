"""Launcher do dashboard ligado ao hardware real (NI-DAQmx) — Fase 5.

Diferente da demo (`janela.abrir()`, adaptador `fake`), este entrypoint monta a
`JanelaMonitor` sobre o `AdaptadorDaqmx`, lendo os canais reais do `canais.toml`.
Roda só no Windows (o `nidaqmx` é carregado lazy dentro do adaptador). Repassa
canais + config à janela para que Aferir e os rótulos funcionem no hardware.
"""

import argparse
import tomllib
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ensaios_ni.apresentacao.monitor import MonitorAoVivo
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
    ):
        super().__init__()
        self._taxa_hz = taxa_hz
        self._bloco = bloco
        self._saida = Path(saida)
        self._capacidade_janela = capacidade_janela
        self._janela: JanelaMonitor | None = None  # mantém a referência (evita fechar por GC)
        self.setWindowTitle("ensaios-ni")

        self._btn_abrir = QPushButton("Abrir configuração…")
        self._btn_abrir.clicked.connect(self._escolher_e_abrir)
        self._lbl_erro = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nenhuma configuração de canais carregada."))
        layout.addWidget(self._btn_abrir)
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
