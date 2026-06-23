from ensaios_ni.dominio.canais import Canal
from ensaios_ni.dominio.conversao import calcular_tara, converter


def _canal(ganho: float, offset: float) -> Canal:
    return Canal(nome="Mod1/ai0", tipo="tensao", unidade="bar", ganho=ganho, offset=offset)


def test_conversao_linear_aplica_ganho_e_offset():
    canal = _canal(ganho=20.0, offset=-5.0)
    assert converter(0.0, canal) == -5.0
    assert converter(1.0, canal) == 15.0


def test_conversao_de_varias_amostras():
    canal = _canal(ganho=2.0, offset=1.0)
    assert [converter(v, canal) for v in [0.0, 1.0, 2.0]] == [1.0, 3.0, 5.0]


def _canal_pontos(pontos) -> Canal:
    return Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", pontos=pontos)


def test_conversao_por_pontos_interpola_entre_os_pontos():
    # célula de carga calibrada: 0 V = 0 kgf, 10 V = 1000 kgf
    canal = _canal_pontos(((0.0, 0.0), (10.0, 1000.0)))
    assert converter(5.0, canal) == 500.0


def test_conversao_por_pontos_usa_o_segmento_certo_em_curva_de_tres_pontos():
    # curva não-linear: inclinação muda no ponto do meio
    canal = _canal_pontos(((0.0, 0.0), (5.0, 100.0), (10.0, 150.0)))
    assert converter(2.5, canal) == 50.0   # primeiro segmento (20 kgf/V)
    assert converter(5.0, canal) == 100.0  # nó central
    assert converter(7.5, canal) == 125.0  # segundo segmento (10 kgf/V)


def test_conversao_por_pontos_clampa_fora_da_faixa():
    canal = _canal_pontos(((0.0, 0.0), (10.0, 1000.0)))
    assert converter(-3.0, canal) == 0.0     # abaixo do menor ponto
    assert converter(12.0, canal) == 1000.0  # acima do maior ponto


def test_calcular_tara_e_a_media_do_repouso_na_unidade():
    canal = _canal(ganho=100.0, offset=0.0)  # kgf
    assert calcular_tara([0.1, 0.1, 0.1], canal) == 10.0


def test_converter_com_tara_desloca_o_resultado():
    canal = _canal(ganho=100.0, offset=0.0)
    assert converter(2.0, canal, tara=10.0) == 190.0  # 200 - 10


def test_em_repouso_a_leitura_tarada_e_zero_mesmo_com_offset():
    # escala que não passa pela origem: a tara ainda zera o repouso (comportamento "Zero Channel")
    canal = _canal(ganho=100.0, offset=5.0)
    repouso = [0.1, 0.1, 0.1]
    tara = calcular_tara(repouso, canal)
    assert converter(0.1, canal, tara=tara) == 0.0
