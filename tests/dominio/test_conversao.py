from ensaios_ni.dominio.canais import Canal
from ensaios_ni.dominio.conversao import converter


def _canal(ganho: float, offset: float) -> Canal:
    return Canal(nome="Mod1/ai0", tipo="tensao", unidade="bar", ganho=ganho, offset=offset)


def test_conversao_linear_aplica_ganho_e_offset():
    canal = _canal(ganho=20.0, offset=-5.0)
    assert converter(0.0, canal) == -5.0
    assert converter(1.0, canal) == 15.0


def test_conversao_de_varias_amostras():
    canal = _canal(ganho=2.0, offset=1.0)
    assert [converter(v, canal) for v in [0.0, 1.0, 2.0]] == [1.0, 3.0, 5.0]
