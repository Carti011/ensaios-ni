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
