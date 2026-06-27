import pytest

from ensaios_ni.apresentacao.afericao import Afericao
from ensaios_ni.dominio.canais import carregar_canais


def test_afericao_ajusta_reta_dos_pontos():
    # núcleo da "Aferição por Regressão Linear" do AqDados: N pontos -> uma reta
    af = Afericao()
    af.adicionar_ponto(0.0, 0.0)
    af.adicionar_ponto(5.0, 500.0)
    af.adicionar_ponto(10.0, 1000.0)

    reta = af.reta()
    assert reta is not None
    assert reta.a == pytest.approx(100.0)
    assert reta.b == pytest.approx(0.0)
    assert reta.correlacao == pytest.approx(1.0)


def test_correlacao_em_percentual_decimal_virgula():
    # o "100,00 %" do AqDados, no padrão BR (vírgula)
    af = Afericao()
    af.adicionar_ponto(0.0, 0.0)
    af.adicionar_ponto(5.0, 500.0)
    af.adicionar_ponto(10.0, 1000.0)
    assert af.correlacao_percentual() == "100,00 %"


def test_sem_pontos_suficientes_nao_ha_reta_nem_correlacao():
    af = Afericao()
    af.adicionar_ponto(1.0, 10.0)
    assert af.reta() is None
    assert af.correlacao_percentual() == "—"


def test_remover_ponto_tira_da_tabela():
    af = Afericao()
    af.adicionar_ponto(0.0, 0.0)
    af.adicionar_ponto(5.0, 500.0)
    af.remover_ponto(0)
    assert af.pontos == [(5.0, 500.0)]


def test_afericao_comeca_com_pontos_existentes_do_canal():
    # a UI abre a aferição de um canal já calibrado mostrando os pontos que ele tem
    af = Afericao(pontos=[(0.0, 0.0), (5.0, 500.0)])
    assert af.pontos == [(0.0, 0.0), (5.0, 500.0)]
    assert af.reta() is not None


def test_ganho_inverso_e_volts_por_unidade():
    # reta.a = un/V (o "Ganho 1/K" do AqDados); ganho_inverso = 1/a = V/un (o "Ganho K")
    af = Afericao(pontos=[(0.0, 0.0), (10.0, 1000.0)])  # a = 100 un/V
    assert af.reta().a == pytest.approx(100.0)
    assert af.ganho_inverso() == pytest.approx(0.01)


def test_reta_none_quando_volts_sem_variacao_nao_quebra_a_ui():
    # estado transitório ao montar a tabela (mesma tensão em dois pontos): sem reta, sem crash
    af = Afericao(pontos=[(0.0, 100.0), (0.0, 200.0)])
    assert af.reta() is None
    assert af.ganho_inverso() is None
    assert af.correlacao_percentual() == "—"


def test_ganho_inverso_sem_reta_ou_com_ganho_zero():
    assert Afericao(pontos=[(1.0, 5.0)]).ganho_inverso() is None  # 1 ponto: sem reta
    assert Afericao(pontos=[(0.0, 5.0), (10.0, 5.0)]).ganho_inverso() is None  # a=0: K indefinido


def test_definir_pontos_substitui_a_tabela_inteira():
    af = Afericao(pontos=[(0.0, 0.0)])
    af.definir_pontos([(0.0, 0.0), (5.0, 500.0), (10.0, 1000.0)])
    assert af.pontos == [(0.0, 0.0), (5.0, 500.0), (10.0, 1000.0)]
    assert af.reta().a == pytest.approx(100.0)


def test_aplicar_persiste_a_afericao_no_toml(tmp_path):
    arq = tmp_path / "canais.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )
    af = Afericao(caminho=arq, canal="Mod1/ai0")
    af.adicionar_ponto(0.0, 0.0)
    af.adicionar_ponto(10.0, 1000.0)
    af.aplicar()

    canal = carregar_canais(arq)["Mod1/ai0"]
    assert canal.reta is not None
    assert canal.reta.a == pytest.approx(100.0)
