import statistics

from ensaios_ni.dominio.filtro import media_movel


def test_media_movel_reduz_o_ruido_mantendo_o_tamanho():
    # ruído de alta frequência (±1 em torno de 1); a média móvel achata a oscilação
    ruidoso = [0.0, 2.0, 0.0, 2.0, 0.0, 2.0, 0.0]
    suave = media_movel(ruidoso, janela=3)
    assert len(suave) == len(ruidoso)  # mesmo nº de pontos: alinha com o eixo de tempo
    assert statistics.pvariance(suave) < statistics.pvariance(ruidoso)


def test_media_movel_janela_um_e_o_filtro_desligado():
    serie = [1.0, 5.0, 3.0, 9.0]
    assert media_movel(serie, janela=1) == serie
