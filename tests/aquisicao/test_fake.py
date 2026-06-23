import pytest

from ensaios_ni.aquisicao.fake import AquisicaoFake


def test_ler_tensao_devolve_um_dict_so_com_os_canais_pedidos():
    fake = AquisicaoFake(
        tensoes={"Mod1/ai0": [1.0, 2.0, 3.0], "Mod1/ai1": [4.0, 5.0, 6.0]}
    )
    leituras = fake.ler_tensao(["Mod1/ai0"], amostras=2, taxa_hz=100.0)
    assert leituras == {"Mod1/ai0": [1.0, 2.0]}


def test_ler_tensao_alinha_varios_canais_no_mesmo_numero_de_amostras():
    fake = AquisicaoFake(
        tensoes={"Mod1/ai0": [1.0, 2.0, 3.0], "Mod1/ai1": [4.0, 5.0, 6.0]}
    )
    leituras = fake.ler_tensao(["Mod1/ai0", "Mod1/ai1"], amostras=2, taxa_hz=100.0)
    assert leituras == {"Mod1/ai0": [1.0, 2.0], "Mod1/ai1": [4.0, 5.0]}


def test_canal_sem_dados_no_fake_falha_claro():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="Mod9/ai9"):
        fake.ler_tensao(["Mod9/ai9"], amostras=1, taxa_hz=100.0)


def test_pedir_mais_amostras_do_que_o_fake_tem_falha():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="pedidas 5"):
        fake.ler_tensao(["Mod1/ai0"], amostras=5, taxa_hz=100.0)


def test_amostras_nao_positivas_falham():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="amostras"):
        fake.ler_tensao(["Mod1/ai0"], amostras=0, taxa_hz=100.0)


def test_taxa_nao_positiva_falha():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0]})
    with pytest.raises(ValueError, match="taxa_hz"):
        fake.ler_tensao(["Mod1/ai0"], amostras=1, taxa_hz=0.0)
