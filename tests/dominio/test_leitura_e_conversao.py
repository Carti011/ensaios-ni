from ensaios_ni.aquisicao.fake import AquisicaoFake
from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.dominio.conversao import converter


def test_le_tensao_do_fake_e_converte_para_unidade_de_engenharia(tmp_path):
    # config: canal de tensão com conversão linear (célula de carga fictícia: 100 kgf/V)
    config = tmp_path / "canais.toml"
    config.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )

    canais = carregar_canais(config)
    fake = AquisicaoFake(tensoes={"Mod1/ai0": [2.0]})

    volts = fake.ler_tensao("Mod1/ai0", amostras=1)
    canal = canais["Mod1/ai0"]
    resultado = [converter(v, canal) for v in volts]

    # 2,0 V * 100 kgf/V + 0 = 200 kgf
    assert resultado == [200.0]
