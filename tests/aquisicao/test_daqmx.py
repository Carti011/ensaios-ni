import sys
import types

from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx
from ensaios_ni.dominio.canais import Canais, Canal, ParametrosStrain


def _canais_strain(params_por_nome):
    return Canais(
        {
            nome: Canal(nome=nome, tipo="strain", unidade="µε", strain=params)
            for nome, params in params_por_nome.items()
        }
    )


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
        self._registro["saiu"].append(True)
        return False

    def add_ai_voltage_chan(self, canal, **kwargs):
        self._registro["canais"].append((canal, kwargs))

    def add_ai_strain_gage_chan(self, canal, **kwargs):
        self._registro["strain"].append((canal, kwargs))

    def cfg_samp_clk_timing(self, **kwargs):
        self._registro["timing"].append(kwargs)

    def read(self, number_of_samples_per_channel):
        self._registro["read"].append(number_of_samples_per_channel)
        return self._dados


def _instalar_nidaqmx_fake(monkeypatch, dados):
    registro = {"canais": [], "strain": [], "timing": [], "read": [], "saiu": []}
    nidaqmx_mod = types.ModuleType("nidaqmx")
    nidaqmx_mod.Task = lambda: _TaskFake(registro, dados)
    constantes = types.ModuleType("nidaqmx.constants")
    constantes.AcquisitionType = types.SimpleNamespace(FINITE="FINITE", CONTINUOUS="CONTINUOUS")
    constantes.TerminalConfiguration = types.SimpleNamespace(DIFF="DIFF", RSE="RSE")
    constantes.StrainGageBridgeType = types.SimpleNamespace(
        QUARTER_BRIDGE_I="QUARTER_BRIDGE_I", FULL_BRIDGE_I="FULL_BRIDGE_I"
    )
    constantes.ExcitationSource = types.SimpleNamespace(INTERNAL="INTERNAL", EXTERNAL="EXTERNAL")
    constantes.StrainUnits = types.SimpleNamespace(STRAIN="STRAIN")
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


def test_le_strain_um_canal_normaliza_lista_simples(monkeypatch):
    _instalar_nidaqmx_fake(monkeypatch, dados=[1e-4, 2e-4, 3e-4])
    leituras = AdaptadorDaqmx().ler_strain(["cDAQ1Mod3/ai0"], amostras=3, taxa_hz=1024.0)
    assert leituras == {"cDAQ1Mod3/ai0": [1e-4, 2e-4, 3e-4]}


def test_le_strain_varios_canais_normaliza_lista_de_listas(monkeypatch):
    _instalar_nidaqmx_fake(monkeypatch, dados=[[1e-4, 2e-4], [3e-4, 4e-4]])
    leituras = AdaptadorDaqmx().ler_strain(
        ["cDAQ1Mod3/ai0", "cDAQ1Mod3/ai1"], amostras=2, taxa_hz=1024.0
    )
    assert leituras == {"cDAQ1Mod3/ai0": [1e-4, 2e-4], "cDAQ1Mod3/ai1": [3e-4, 4e-4]}


def test_strain_usa_parametros_do_9235_nunca_os_defaults_da_api(monkeypatch):
    # ARMADILHA PRINCIPAL DO PROJETO: defaults da API (full-bridge 350 Ω / 2,5 V) dão
    # número plausível e ERRADO sem lançar erro. Este teste trava isso.
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1e-4])
    AdaptadorDaqmx().ler_strain(["cDAQ1Mod3/ai0"], amostras=1, taxa_hz=1024.0)

    assert registro["strain"], "add_ai_strain_gage_chan não foi chamado"
    _, kwargs = registro["strain"][0]
    assert kwargs["strain_config"] == "QUARTER_BRIDGE_I"   # nunca FULL_BRIDGE
    assert kwargs["nominal_gage_resistance"] == 120.0       # nunca 350
    assert kwargs["voltage_excit_val"] == 2.0               # nunca 2,5
    assert kwargs["voltage_excit_source"] == "INTERNAL"
    assert kwargs["units"] == "STRAIN"
    assert kwargs["gage_factor"] == 2.15                    # default seguro (configurável)


def test_strain_usa_parametros_do_canal(monkeypatch):
    # o gage factor (e demais parâmetros) vêm da config do canal, não fixos no código
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1e-4])
    canais = _canais_strain(
        {"cDAQ1Mod3/ai0": ParametrosStrain(gage_factor=2.14, lead_wire_resistance=1.2)}
    )
    AdaptadorDaqmx(canais=canais).ler_strain(["cDAQ1Mod3/ai0"], amostras=1, taxa_hz=1024.0)

    _, kwargs = registro["strain"][0]
    assert kwargs["gage_factor"] == 2.14
    assert kwargs["lead_wire_resistance"] == 1.2


def test_strain_aplica_parametros_por_canal(monkeypatch):
    # cada extensômetro tem seu gage factor (varia por lote): cada task usa o do seu canal
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[[1e-4], [2e-4]])
    canais = _canais_strain(
        {
            "cDAQ1Mod3/ai0": ParametrosStrain(gage_factor=2.14),
            "cDAQ1Mod3/ai1": ParametrosStrain(gage_factor=2.16),
        }
    )
    AdaptadorDaqmx(canais=canais).ler_strain(
        ["cDAQ1Mod3/ai0", "cDAQ1Mod3/ai1"], amostras=1, taxa_hz=1024.0
    )

    factors = [kwargs["gage_factor"] for _, kwargs in registro["strain"]]
    assert factors == [2.14, 2.16]


def test_strain_sem_canais_usa_defaults_seguros(monkeypatch):
    # sem config de canal, cai no default seguro do 9235 (nunca os da API)
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1e-4])
    AdaptadorDaqmx().ler_strain(["cDAQ1Mod3/ai0"], amostras=1, taxa_hz=1024.0)

    _, kwargs = registro["strain"][0]
    assert kwargs["gage_factor"] == 2.15
    assert kwargs["strain_config"] == "QUARTER_BRIDGE_I"
    assert kwargs["nominal_gage_resistance"] == 120.0


def test_strain_configura_sample_clock(monkeypatch):
    # guarda contra regressão pro on-demand (que falha no 9235 no chassi Ethernet)
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1e-4])
    AdaptadorDaqmx().ler_strain(["cDAQ1Mod3/ai0"], amostras=1, taxa_hz=1024.0)
    assert registro["timing"], "cfg_samp_clk_timing não foi chamado no strain"
    assert registro["timing"][0]["rate"] == 1024.0
    assert registro["timing"][0]["samps_per_chan"] == 1


def test_transmitir_tensao_modo_continuous_emite_blocos_e_encerra_limpo(monkeypatch):
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1.0, 2.0])
    fluxo = AdaptadorDaqmx().transmitir_tensao(
        ["cDAQ1Mod1/ai0"], taxa_hz=1024.0, amostras_por_bloco=2
    )
    assert next(fluxo) == {"cDAQ1Mod1/ai0": [1.0, 2.0]}
    assert registro["timing"][0]["sample_mode"] == "CONTINUOUS"
    assert registro["read"][0] == 2
    fluxo.close()  # ao fechar o fluxo, a task é encerrada (with __exit__)
    assert registro["saiu"] == [True]


def test_transmitir_strain_usa_parametros_do_9235_em_modo_continuous(monkeypatch):
    # a armadilha do strain vale também no contínuo: nunca os defaults da API
    registro = _instalar_nidaqmx_fake(monkeypatch, dados=[1e-4, 2e-4])
    fluxo = AdaptadorDaqmx().transmitir_strain(
        ["cDAQ1Mod3/ai0"], taxa_hz=1024.0, amostras_por_bloco=2
    )
    assert next(fluxo) == {"cDAQ1Mod3/ai0": [1e-4, 2e-4]}
    assert registro["timing"][0]["sample_mode"] == "CONTINUOUS"
    _, kwargs = registro["strain"][0]
    assert kwargs["strain_config"] == "QUARTER_BRIDGE_I"
    assert kwargs["nominal_gage_resistance"] == 120.0
    assert kwargs["voltage_excit_val"] == 2.0
    fluxo.close()
