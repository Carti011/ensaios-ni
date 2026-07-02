from ensaios_ni.apresentacao.erros import mensagem_de_erro_de_aquisicao


def test_driver_ausente_orienta_instalar_o_ni_daqmx():
    # no Mac (e no Windows do tio sem o driver) o Iniciar estoura ModuleNotFoundError
    erro = ModuleNotFoundError("No module named 'nidaqmx'", name="nidaqmx")
    msg = mensagem_de_erro_de_aquisicao(erro)
    assert "NI-DAQmx" in msg
    assert "instal" in msg.lower()  # orienta instalar o driver


class _DaqErrorFalso(Exception):
    """Simula um erro do driver NI sem depender do nidaqmx (que não existe no Mac)."""


_DaqErrorFalso.__module__ = "nidaqmx.errors"


def test_erro_do_driver_ni_aponta_o_ni_max_e_preserva_o_detalhe():
    # chassi fora da rede / canal inexistente no HW sobem como DaqError do nidaqmx
    erro = _DaqErrorFalso("Device cannot be accessed. Status Code: -201003")
    msg = mensagem_de_erro_de_aquisicao(erro)
    assert "NI-MAX" in msg  # onde o tio confere o chassi
    assert "-201003" in msg  # detalhe técnico preservado para diagnóstico


def test_erro_inesperado_cai_no_fallback_preservando_o_detalhe():
    # erro não reconhecido (ex.: o ValueError do fake) não é engolido: mantém o texto original
    erro = ValueError("canal 'Mod9/ai9' não tem dados sintéticos no fake")
    msg = mensagem_de_erro_de_aquisicao(erro)
    assert "Mod9/ai9" in msg


def test_canal_inexistente_orienta_conferir_os_nomes_no_config():
    # DAQmx quando um canal do config não existe no equipamento (nome errado no canais.toml)
    erro = _DaqErrorFalso("Physical channel specified does not exist. Status Code: -200170")
    msg = mensagem_de_erro_de_aquisicao(erro)
    assert "canais.toml" in msg
    assert "NI-MAX" in msg
    assert "-200170" in msg  # detalhe técnico preservado


def test_chassi_nao_encontrado_orienta_rede_e_ni_max():
    # DAQmx quando o chassi Ethernet não responde (desligado, cabo, IP errado)
    erro = _DaqErrorFalso("Device cannot be found. Verify it is connected. Status Code: -200220")
    msg = mensagem_de_erro_de_aquisicao(erro)
    assert "chassi" in msg.lower()
    assert any(p in msg.lower() for p in ("rede", "cabo", "ip"))
    assert "-200220" in msg
