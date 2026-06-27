import os

import pytest

# o widget só existe com o extra [gui]; sem PySide/pyqtgraph, pula (domínio não depende disso)
pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # roda headless, sem display

from ensaios_ni.apresentacao.monitor import EstadoMonitor, MonitorAoVivo  # noqa: E402
from ensaios_ni.apresentacao.qt.janela import JanelaMonitor  # noqa: E402
from ensaios_ni.aquisicao.fake import AquisicaoFake  # noqa: E402
from ensaios_ni.dominio.canais import Canais, Canal  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _monitor(tmp_path) -> MonitorAoVivo:
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    canais = Canais(
        {"Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0)}
    )
    return MonitorAoVivo(
        fonte, canais, taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )


def test_janela_monta_inicia_e_processa_um_passo(app, tmp_path):
    janela = JanelaMonitor(_monitor(tmp_path))
    janela.iniciar()
    assert janela._monitor.estado is EstadoMonitor.ADQUIRINDO
    janela._ao_passo()
    assert janela._monitor.valor_atual("Mod1/ai0") == 20.0
    janela.parar()
    assert janela._monitor.estado is EstadoMonitor.PARADO
