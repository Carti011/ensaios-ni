import sys
import types

from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx


class _TaskFake:
    """Imita o nidaqmx.Task: registra as chamadas e devolve dados controlados.

    `task.ai_channels` e `task.timing` apontam para o próprio objeto — basta
    para verificar como o adaptador monta a task, sem o nidaqmx instalado.
    """

    def __init__(self, registro, dados):
        self._registro = registro
        self._dados = dados
        self.ai_channels = self
        self.timing = self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add_ai_voltage_chan(self, canal, **kwargs):
        self._registro["canais"].append((canal, kwargs))

    def cfg_samp_clk_timing(self, **kwargs):
        self._registro["timing"].append(kwargs)

    def read(self, number_of_samples_per_channel):
        self._registro["read"].append(number_of_samples_per_channel)
        return self._dados


def _instalar_nidaqmx_fake(monkeypatch, dados):
    registro = {"canais": [], "timing": [], "read": []}
    nidaqmx_mod = types.ModuleType("nidaqmx")
    nidaqmx_mod.Task = lambda: _TaskFake(registro, dados)
    constantes = types.ModuleType("nidaqmx.constants")
    constantes.AcquisitionType = types.SimpleNamespace(FINITE="FINITE", CONTINUOUS="CONTINUOUS")
    constantes.TerminalConfiguration = types.SimpleNamespace(DIFF="DIFF", RSE="RSE")
    nidaqmx_mod.constants = constantes
    monkeypatch.setitem(sys.modules, "nidaqmx", nidaqmx_mod)
    monkeypatch.setitem(sys.modules, "nidaqmx.constants", constantes)
    return registro


def test_le_um_canal_normaliza_lista_simples(monkeypatch):
    _instalar_nidaqmx_fake(monkeypatch, dados=[1.0, 2.0, 3.0])
    leituras = AdaptadorDaqmx().ler_tensao(["cDAQ1Mod1/ai0"], amostras=3, taxa_hz=1024.0)
    assert leituras == {"cDAQ1Mod1/ai0": [1.0, 2.0, 3.0]}


def test_le_varios_canais_normaliza_lista_de_listas_alinhada(monkeypatch):
    _instalar_nidaqmx_fake(monkeypatch, dados=[[1.0, 2.0], [3.0, 4.0]])
    leituras = AdaptadorDaqmx().ler_tensao(
        ["cDAQ1Mod1/ai0", "cDAQ1Mod1/ai1"], amostras=2, taxa_hz=1024.0
    )
    assert leituras == {"cDAQ1Mod1/ai0": [1.0, 2.0], "cDAQ1Mod1/ai1": [3.0, 4.0]}


def test_configura_sample_clock_com_a_taxa(monkeypatch):
    # guarda contra regressão pro on-demand (que falha no 9235 no chassi Ethernet)
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1.0])
    AdaptadorDaqmx().ler_tensao(["cDAQ1Mod1/ai0"], amostras=1, taxa_hz=1024.0)
    assert registro["timing"], "cfg_samp_clk_timing não foi chamado"
    timing = registro["timing"][0]
    assert timing["rate"] == 1024.0
    assert timing["samps_per_chan"] == 1


def test_adiciona_um_canal_de_tensao_por_canal_pedido_com_a_faixa(monkeypatch):
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[[1.0], [2.0]])
    AdaptadorDaqmx(min_val=-5.0, max_val=5.0).ler_tensao(
        ["cDAQ1Mod1/ai0", "cDAQ1Mod1/ai1"], amostras=1, taxa_hz=1000.0
    )
    nomes = [canal for canal, _ in registro["canais"]]
    assert nomes == ["cDAQ1Mod1/ai0", "cDAQ1Mod1/ai1"]
    _, kwargs = registro["canais"][0]
    assert kwargs["min_val"] == -5.0
    assert kwargs["max_val"] == 5.0
