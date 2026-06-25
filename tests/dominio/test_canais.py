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


def test_config_com_pontos_usa_regressao_por_default(tmp_path):
    # padrão do AqDados: pontos -> regressão linear (uma reta + correlação)
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[0.0, 0.0], [5.0, 500.0], [10.0, 1000.0]]\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.pontos is None
    assert canal.reta.a == pytest.approx(100.0)
    assert canal.reta.b == pytest.approx(0.0)
    assert canal.reta.correlacao == pytest.approx(1.0)


def test_config_regressao_aceita_volts_repetido_de_medicoes(tmp_path):
    # regressão tolera medições repetidas no mesmo ponto (não é ambíguo como no segmento)
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[1.0, 100.0], [1.0, 102.0], [2.0, 200.0]]\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.reta is not None
    assert canal.reta.correlacao < 1.0


def test_config_metodo_segmento_mantem_interpolacao_por_pontos(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'metodo = "segmento"\n'
        'pontos = [[10.0, 1000.0], [0.0, 0.0], [5.0, 400.0]]\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.pontos == ((0.0, 0.0), (5.0, 400.0), (10.0, 1000.0))  # ordenado
    assert canal.reta is None


def test_config_metodo_invalido_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'metodo = "spline"\n'
        'pontos = [[0.0, 0.0], [10.0, 1000.0]]\n'
    )
    with pytest.raises(ConfiguracaoInvalida) as exc:
        carregar_canais(_escrever(tmp_path, conteudo))
    assert "Mod1/ai0" in str(exc.value) and "spline" in str(exc.value)


def test_config_metodo_sem_pontos_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'metodo = "regressao"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
    )
    with pytest.raises(ConfiguracaoInvalida, match="metodo"):
        carregar_canais(_escrever(tmp_path, conteudo))


def test_config_com_menos_de_dois_pontos_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[0.0, 0.0]]\n'
    )
    with pytest.raises(ConfiguracaoInvalida, match="Mod1/ai0"):
        carregar_canais(_escrever(tmp_path, conteudo))


def test_config_segmento_com_volts_repetido_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'metodo = "segmento"\n'
        'pontos = [[0.0, 0.0], [0.0, 500.0]]\n'  # mesmo volts, ambíguo na interpolação
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


def test_config_com_tipo_desconhecido_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "vibracao"\n'  # nem tensao nem strain
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
    )
    with pytest.raises(ConfiguracaoInvalida) as exc:
        carregar_canais(_escrever(tmp_path, conteudo))
    msg = str(exc.value)
    assert "Mod1/ai0" in msg and "vibracao" in msg


def test_config_aceita_tipo_strain(tmp_path):
    conteudo = (
        '[canais."Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'ganho = 1000000.0\n'
        'offset = 0.0\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod3/ai0"]
    assert canal.tipo == "strain"
