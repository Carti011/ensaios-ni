import pytest

from ensaios_ni.dominio.regressao import Reta, ajustar_regressao


def test_pontos_perfeitamente_lineares_dao_reta_exata_e_correlacao_um():
    reta = ajustar_regressao([(0.0, 0.0), (1.0, 2.0), (2.0, 4.0)])

    assert reta.a == pytest.approx(2.0)
    assert reta.b == pytest.approx(0.0)
    assert reta.correlacao == pytest.approx(1.0)


def test_reta_aplica_a_volts():
    reta = Reta(a=2.0, b=1.0, correlacao=1.0)
    assert reta.aplicar(3.0) == pytest.approx(7.0)


def test_pontos_com_ruido_ajustam_por_minimos_quadrados_e_correlacao_menor_que_um():
    reta = ajustar_regressao([(0.0, 0.1), (1.0, 1.9), (2.0, 4.1)])

    assert reta.a == pytest.approx(2.0)
    assert reta.b == pytest.approx(0.1 / 3)  # não passa pelo ponto (0, 0.1)
    assert reta.correlacao == pytest.approx(0.99834, abs=1e-4)


def test_correlacao_um_quando_todos_os_valores_de_engenharia_sao_iguais():
    reta = ajustar_regressao([(1.0, 5.0), (2.0, 5.0), (3.0, 5.0)])

    assert reta.a == pytest.approx(0.0)
    assert reta.b == pytest.approx(5.0)
    assert reta.correlacao == 1.0
