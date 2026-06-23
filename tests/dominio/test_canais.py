import pytest

from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.dominio.erros import CanalNaoConfigurado, ConfiguracaoInvalida

CONFIG_OK = (
    '[canais."Mod1/ai0"]\n'
    'tipo = "tensao"\n'
    'unidade = "kgf"\n'
    'ganho = 100.0\n'
    'offset = 0.0\n'
)


def _escrever(tmp_path, conteudo):
    arq = tmp_path / "canais.toml"
    arq.write_text(conteudo, encoding="utf-8")
    return arq


def test_canal_fora_da_config_lanca_erro_de_dominio(tmp_path):
    canais = carregar_canais(_escrever(tmp_path, CONFIG_OK))
    with pytest.raises(CanalNaoConfigurado, match="Mod9/ai9"):
        canais["Mod9/ai9"]


def test_config_sem_campo_obrigatorio_aponta_canal_e_campo(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'offset = 0.0\n'  # falta ganho
    )
    with pytest.raises(ConfiguracaoInvalida) as exc:
        carregar_canais(_escrever(tmp_path, conteudo))
    msg = str(exc.value)
    assert "Mod1/ai0" in msg and "ganho" in msg


def test_config_com_ganho_nao_numerico_aponta_canal_e_campo(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = "muito"\n'  # ganho não numérico
        'offset = 0.0\n'
    )
    with pytest.raises(ConfiguracaoInvalida) as exc:
        carregar_canais(_escrever(tmp_path, conteudo))
    msg = str(exc.value)
    assert "Mod1/ai0" in msg and "ganho" in msg


def test_config_com_pontos_carrega_calibracao_por_pontos(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[0.0, 0.0], [10.0, 1000.0]]\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.pontos == ((0.0, 0.0), (10.0, 1000.0))
    assert canal.ganho is None and canal.offset is None


def test_config_com_pontos_fora_de_ordem_ordena_por_volts(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[10.0, 1000.0], [0.0, 0.0], [5.0, 400.0]]\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.pontos == ((0.0, 0.0), (5.0, 400.0), (10.0, 1000.0))


def test_config_com_menos_de_dois_pontos_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[0.0, 0.0]]\n'
    )
    with pytest.raises(ConfiguracaoInvalida, match="Mod1/ai0"):
        carregar_canais(_escrever(tmp_path, conteudo))


def test_config_com_volts_repetido_nos_pontos_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[0.0, 0.0], [0.0, 500.0]]\n'  # mesmo volts, ambíguo
    )
    with pytest.raises(ConfiguracaoInvalida, match="Mod1/ai0"):
        carregar_canais(_escrever(tmp_path, conteudo))


def test_config_sem_pontos_e_sem_ganho_offset_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
    )
    with pytest.raises(ConfiguracaoInvalida, match="Mod1/ai0"):
        carregar_canais(_escrever(tmp_path, conteudo))
