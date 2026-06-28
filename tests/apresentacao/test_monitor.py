import pytest

from ensaios_ni.apresentacao.monitor import AquisicaoEmAndamento, EstadoMonitor, MonitorAoVivo
from ensaios_ni.aquisicao.fake import AquisicaoFake
from ensaios_ni.dominio.canais import Canais, Canal
from ensaios_ni.persistencia.csv_ensaio import carregar_csv


def _canais_tensao() -> Canais:
    return Canais(
        {"Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0)}
    )


def _canais_tensao_e_strain() -> Canais:
    return Canais(
        {
            "Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0),
            "Mod3/ai0": Canal(
                nome="Mod3/ai0", tipo="strain", unidade="µε", ganho=1_000_000.0, offset=0.0
            ),
        }
    )


def test_processar_bloco_expoe_valores_convertidos_e_tempo(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    monitor.passo()
    quadro = monitor.quadro()
    assert quadro.tempos == [0.0, 0.25]
    assert quadro.dados["Mod1/ai0"] == [10.0, 20.0]


def test_janela_deslizante_mantem_os_ultimos_pontos_com_tempo_absoluto(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})
    monitor = MonitorAoVivo(
        fonte,
        _canais_tensao(),
        taxa_hz=1.0,
        amostras_por_bloco=2,
        caminho=tmp_path / "e.csv",
        capacidade_janela=3,
    )
    monitor.iniciar()
    monitor.passo()
    monitor.passo()
    monitor.passo()
    quadro = monitor.quadro()
    assert quadro.tempos == [3.0, 4.0, 5.0]
    assert quadro.dados["Mod1/ai0"] == [40.0, 50.0, 60.0]


def test_costura_tensao_e_strain_na_ordem_do_config(tmp_path):
    fonte = AquisicaoFake(
        tensoes={"Mod1/ai0": [1.0, 2.0]},
        strains={"Mod3/ai0": [0.001, 0.001]},
    )
    monitor = MonitorAoVivo(
        fonte, _canais_tensao_e_strain(), taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    monitor.passo()
    quadro = monitor.quadro()
    assert list(quadro.dados.keys()) == ["Mod1/ai0", "Mod3/ai0"]
    assert quadro.dados["Mod1/ai0"] == [10.0, 20.0]
    assert quadro.dados["Mod3/ai0"] == [1000.0, 1000.0]


def test_erro_na_aquisicao_vai_para_estado_erro_sem_estourar(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]})
    canais = Canais(
        {"Mod9/ai9": Canal(nome="Mod9/ai9", tipo="tensao", unidade="kgf", ganho=1.0, offset=0.0)}
    )
    monitor = MonitorAoVivo(
        fonte, canais, taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    assert monitor.passo() is False
    assert monitor.estado is EstadoMonitor.ERRO
    assert "Mod9/ai9" in monitor.erro


def test_quando_a_fonte_esgota_para_limpo_e_o_csv_fica_integro(tmp_path):
    caminho = tmp_path / "e.csv"
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=2.0, amostras_por_bloco=2, caminho=caminho
    )
    monitor.iniciar()
    assert monitor.passo() is True
    assert monitor.passo() is False
    assert monitor.estado is EstadoMonitor.PARADO
    assert carregar_csv(caminho).dados["Mod1/ai0"] == [10.0, 20.0]


def test_valor_atual_e_a_ultima_amostra_convertida(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    assert monitor.valor_atual("Mod1/ai0") is None
    monitor.iniciar()
    monitor.passo()
    assert monitor.valor_atual("Mod1/ai0") == 20.0
    monitor.passo()
    assert monitor.valor_atual("Mod1/ai0") == 40.0


def test_grava_csv_dos_blocos_convertidos_e_fecha_ao_parar(tmp_path):
    caminho = tmp_path / "e.csv"
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=caminho
    )
    monitor.iniciar()
    monitor.passo()
    monitor.passo()
    monitor.parar()
    serie = carregar_csv(caminho)
    assert serie.dados["Mod1/ai0"] == [10.0, 20.0, 30.0, 40.0]
    assert serie.unidades["Mod1/ai0"] == "kgf"


def test_reiniciar_zera_o_tempo_e_limpa_a_janela(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    monitor.passo()
    monitor.passo()
    monitor.parar()
    monitor.iniciar()  # novo ensaio: recomeça do zero
    monitor.passo()
    quadro = monitor.quadro()
    assert quadro.tempos == [0.0, 0.25]
    assert quadro.dados["Mod1/ai0"] == [10.0, 20.0]


def test_recarregar_canais_aplica_a_nova_calibracao_no_proximo_ensaio(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    novos = Canais(
        {"Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=5.0, offset=0.0)}
    )
    monitor.recarregar_canais(novos)  # aferiu fora e aplicou: a nova calibração vale do próximo Iniciar
    monitor.iniciar()
    monitor.passo()
    assert monitor.quadro().dados["Mod1/ai0"] == [5.0, 10.0]  # ganho 5, não o 10 antigo


def test_recarregar_canais_e_recusado_durante_a_aquisicao(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    novos = Canais(
        {"Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=5.0, offset=0.0)}
    )
    with pytest.raises(AquisicaoEmAndamento):
        monitor.recarregar_canais(novos)
    monitor.passo()  # o ensaio em curso segue com a calibração antiga (ganho 10)
    assert monitor.quadro().dados["Mod1/ai0"] == [10.0, 20.0]


def test_zerar_tara_os_canais_capturando_o_repouso(tmp_path):
    # Zero Channel: com a peça em repouso, o bloco lido vira o zero (referencia-flexlogger §2)
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [2.0, 2.0, 5.0, 6.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    monitor.zerar()
    monitor.passo()  # repouso [2.0, 2.0] -> 20 cada (ganho 10); tara = 20 -> zera
    assert monitor.quadro().dados["Mod1/ai0"] == [0.0, 0.0]
    monitor.passo()  # [5.0, 6.0] -> 50, 60 menos a tara 20
    assert monitor.quadro().dados["Mod1/ai0"] == [0.0, 0.0, 30.0, 40.0]


def test_reiniciar_limpa_a_tara(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [2.0, 2.0, 2.0, 2.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    monitor.iniciar()
    monitor.zerar()
    monitor.passo()  # tara capturada (repouso 2.0)
    monitor.parar()
    monitor.iniciar()  # novo ensaio: sem zero herdado
    monitor.passo()
    assert monitor.quadro().dados["Mod1/ai0"] == [20.0, 20.0]  # ganho 10, sem tara


def test_estado_transita_parado_adquirindo_parado(tmp_path):
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]})
    monitor = MonitorAoVivo(
        fonte, _canais_tensao(), taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )
    assert monitor.estado is EstadoMonitor.PARADO
    monitor.iniciar()
    assert monitor.estado is EstadoMonitor.ADQUIRINDO
    monitor.parar()
    assert monitor.estado is EstadoMonitor.PARADO
