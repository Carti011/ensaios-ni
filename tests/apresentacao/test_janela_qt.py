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


def _monitor_multiunidade(tmp_path) -> MonitorAoVivo:
    fonte = AquisicaoFake(
        tensoes={"Mod1/ai0": [1.0, 2.0], "Mod1/ai1": [1.0, 2.0]},
        strains={"Mod3/ai0": [0.001, 0.001]},
    )
    canais = Canais(
        {
            "Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0),
            "Mod1/ai1": Canal(nome="Mod1/ai1", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0),
            "Mod3/ai0": Canal(
                nome="Mod3/ai0", tipo="strain", unidade="µε", ganho=1_000_000.0, offset=0.0
            ),
        }
    )
    return MonitorAoVivo(
        fonte, canais, taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )


def test_janela_monta_inicia_e_processa_um_passo(app, tmp_path):
    janela = JanelaMonitor(_monitor(tmp_path))
    janela.iniciar()
    assert janela._monitor.estado is EstadoMonitor.ADQUIRINDO
    janela._ao_passo()
    assert janela._monitor.valor_atual("Mod1/ai0") == 20.0
    janela.parar()
    assert janela._monitor.estado is EstadoMonitor.PARADO


def test_janela_empilha_um_subplot_por_unidade(app, tmp_path):
    janela = JanelaMonitor(_monitor_multiunidade(tmp_path))
    # dois canais kgf dividem um sub-plot; µε no seu próprio → 2 sub-plots, não 3
    assert list(janela._graficos.keys()) == ["kgf", "µε"]
    janela.iniciar()
    janela._ao_passo()
    assert janela._monitor.valor_atual("Mod3/ai0") == 1000.0
    janela.parar()


def test_janela_plota_xy_carga_deformacao(app, tmp_path):
    janela = JanelaMonitor(_monitor_multiunidade(tmp_path))
    # default: carga (primeiro canal) no X, deformação (último) no Y
    assert janela._canal_x == "Mod1/ai0"
    assert janela._canal_y == "Mod3/ai0"
    janela.iniciar()
    janela._ao_passo()
    par = janela._par_xy_atual()
    assert par is not None
    assert len(par.xs) == len(par.ys) > 0
    janela.parar()
