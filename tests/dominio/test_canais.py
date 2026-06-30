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


def test_config_regressao_com_volts_todos_iguais_e_invalida(tmp_path):
    # regressão tolera volts repetido se houver variação; mas TODOS iguais é reta indeterminada
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[2.0, 10.0], [2.0, 20.0]]\n'
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


def test_config_carrega_rotulo_nome_do_sinal(tmp_path):
    # "Nome do Sinal" do AqDados: apelido humano do canal, separado do endereço físico
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = "Carga"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.rotulo == "Carga"


def test_etiqueta_usa_rotulo_ou_cai_no_endereco(tmp_path):
    # a UI mostra a etiqueta; sem rótulo, cai no endereço físico (o tio não reconhece o endereço)
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = "Carga"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
        '\n'
        '[canais."Mod1/ai1"]\n'
        'tipo = "tensao"\n'
        'unidade = "bar"\n'
        'ganho = 25.0\n'
        'offset = 0.0\n'
    )
    canais = carregar_canais(_escrever(tmp_path, conteudo))
    assert canais["Mod1/ai0"].etiqueta == "Carga"
    assert canais["Mod1/ai1"].etiqueta == "Mod1/ai1"


def test_config_com_rotulo_nao_string_e_invalida(tmp_path):
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = 42\n'  # rótulo deve ser texto
        'ganho = 100.0\n'
        'offset = 0.0\n'
    )
    with pytest.raises(ConfiguracaoInvalida) as exc:
        carregar_canais(_escrever(tmp_path, conteudo))
    msg = str(exc.value)
    assert "Mod1/ai0" in msg and "rotulo" in msg


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


def test_strain_carrega_gage_factor_do_toml(tmp_path):
    # gage factor varia por lote do extensômetro (2,14–2,16) -> vem da config, não do código
    conteudo = (
        '[canais."Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'gage_factor = 2.14\n'
        'ganho = 1000000.0\n'
        'offset = 0.0\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod3/ai0"]
    assert canal.strain is not None
    assert canal.strain.gage_factor == 2.14


def test_strain_sem_parametros_usa_defaults_seguros_do_9235(tmp_path):
    # ARMADILHA: omitir os campos cai nos defaults do 9235, NUNCA nos da API (full-bridge 350 Ω / 2,5 V)
    conteudo = (
        '[canais."Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'ganho = 1000000.0\n'
        'offset = 0.0\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod3/ai0"]
    assert canal.strain is not None
    assert canal.strain.nominal_gage_resistance == 120.0
    assert canal.strain.voltage_excit_val == 2.0
    assert canal.strain.bridge_config == "QUARTER_BRIDGE_I"


def test_strain_carrega_demais_parametros_do_toml(tmp_path):
    # poisson (material), resistência do gage e do cabo (3 fios) também vêm da config
    conteudo = (
        '[canais."Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'gage_factor = 2.16\n'
        'poisson = 0.28\n'
        'resistencia = 350.0\n'
        'resistencia_cabo = 1.5\n'
        'ganho = 1000000.0\n'
        'offset = 0.0\n'
    )
    strain = carregar_canais(_escrever(tmp_path, conteudo))["Mod3/ai0"].strain
    assert strain.gage_factor == 2.16
    assert strain.poisson_ratio == 0.28
    assert strain.nominal_gage_resistance == 350.0
    assert strain.lead_wire_resistance == 1.5


def test_strain_com_parametro_nao_numerico_aponta_canal_e_campo(tmp_path):
    conteudo = (
        '[canais."Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'gage_factor = "alto"\n'  # deve ser número
        'ganho = 1000000.0\n'
        'offset = 0.0\n'
    )
    with pytest.raises(ConfiguracaoInvalida) as exc:
        carregar_canais(_escrever(tmp_path, conteudo))
    msg = str(exc.value)
    assert "Mod3/ai0" in msg and "gage_factor" in msg


def test_tensao_ignora_parametros_de_strain(tmp_path):
    # gage_factor num canal de tensão não tem efeito (strain fica None)
    conteudo = (
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'gage_factor = 2.14\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
    )
    canal = carregar_canais(_escrever(tmp_path, conteudo))["Mod1/ai0"]
    assert canal.strain is None
