import pytest

from ensaios_ni.apresentacao.tempo import formatar_duracao, parsear_tempo


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("", None),  # vazio = sem limite (o ensaio inteiro)
        ("   ", None),
        ("93600", 93600.0),  # segundos puros
        ("93600,5", 93600.5),  # decimal BR (vírgula)
        ("90.5", 90.5),  # decimal com ponto também
        ("26:00:00", 93600.0),  # hh:mm:ss (26 h)
        ("0:05:00", 300.0),  # 5 min
        ("1:02:00:00", 93600.0),  # dd:hh:mm:ss (1 d 2 h = 26 h)
        ("lixo", None),  # inválido = sem limite, não quebra
        ("1:2:3:4:5", None),  # componentes demais
    ],
)
def test_parsear_tempo(texto, esperado):
    assert parsear_tempo(texto) == esperado


@pytest.mark.parametrize(
    "segundos, esperado",
    [
        (0, "0 s"),
        (45, "45 s"),
        (300, "5 min"),
        (3600, "1 h"),
        (93600, "1 d 2 h"),  # 1 dia 2 h
        (183300, "2 d 2 h 55 min"),  # componentes não-zero
        (52428, "14 h 33 min 48 s"),  # ~ o limite do Excel a 20 Hz
    ],
)
def test_formatar_duracao(segundos, esperado):
    assert formatar_duracao(segundos) == esperado
