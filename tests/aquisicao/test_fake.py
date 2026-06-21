import pytest

from ensaios_ni.aquisicao.fake import AquisicaoFake


def test_ler_tensao_devolve_as_amostras_injetadas():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0]})
    assert fake.ler_tensao("Mod1/ai0", amostras=2) == [1.0, 2.0]


def test_canal_sem_dados_no_fake_falha_claro():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="Mod9/ai9"):
        fake.ler_tensao("Mod9/ai9", amostras=1)


def test_pedir_mais_amostras_do_que_o_fake_tem_falha():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="pedidas 5"):
        fake.ler_tensao("Mod1/ai0", amostras=5)


def test_amostras_nao_positivas_falham():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="amostras"):
        fake.ler_tensao("Mod1/ai0", amostras=0)
