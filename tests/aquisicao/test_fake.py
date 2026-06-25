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


def test_ler_strain_devolve_strain_sintetico_por_canal():
    # strain é adimensional (o driver real já aplica gage factor/ponte)
    fake = AquisicaoFake(strains={"Mod3/ai0": [1e-4, 2e-4, 3e-4]})
    leituras = fake.ler_strain(["Mod3/ai0"], amostras=2, taxa_hz=1024.0)
    assert leituras == {"Mod3/ai0": [1e-4, 2e-4]}


def test_canal_sem_dados_de_strain_no_fake_falha_claro():
    fake = AquisicaoFake(strains={"Mod3/ai0": [1e-4]})
    with pytest.raises(ValueError, match="Mod3/ai9"):
        fake.ler_strain(["Mod3/ai9"], amostras=1, taxa_hz=1024.0)


def test_transmitir_tensao_emite_blocos_completos():
    # 5 amostras em blocos de 2 -> 2 blocos completos; a sobra parcial é descartada
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0, 5.0]})
    blocos = list(fake.transmitir_tensao(["Mod1/ai0"], taxa_hz=10.0, amostras_por_bloco=2))
    assert blocos == [{"Mod1/ai0": [1.0, 2.0]}, {"Mod1/ai0": [3.0, 4.0]}]


def test_transmitir_canal_sem_dados_no_fake_falha_claro():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]})
    fluxo = fake.transmitir_tensao(["Mod9/ai9"], taxa_hz=10.0, amostras_por_bloco=1)
    with pytest.raises(ValueError, match="Mod9/ai9"):
        next(fluxo)


def test_transmitir_bloco_nao_positivo_falha():
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]})
    fluxo = fake.transmitir_tensao(["Mod1/ai0"], taxa_hz=10.0, amostras_por_bloco=0)
    with pytest.raises(ValueError, match="amostras_por_bloco"):
        next(fluxo)
