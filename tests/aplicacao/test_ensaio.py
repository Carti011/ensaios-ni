from ensaios_ni.aplicacao.ensaio import executar_ensaio
from ensaios_ni.aquisicao.fake import AquisicaoFake
from ensaios_ni.dominio.canais import Canais, Canal


def test_le_converte_e_grava_csv_com_unidade(tmp_path):
    fonte = AquisicaoFake({"Mod1/ai0": [2.0, 2.5]})
    canais = Canais({"Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0)})
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio(fonte, canais, amostras=2, taxa_hz=10.0, caminho=caminho)

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf)\n"
        "0.0,200.0\n"
        "0.1,250.0\n"
    )


def test_ensaio_aplica_tara_capturada_no_repouso(tmp_path):
    # repouso: 1ª amostra (1,0 V -> 100 kgf) vira a tara; ensaio: [1,0 V, 3,0 V] - tara
    fonte = AquisicaoFake({"Mod1/ai0": [1.0, 3.0]})
    canais = Canais({"Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0)})
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio(
        fonte, canais, amostras=2, taxa_hz=10.0, caminho=caminho, amostras_tara=1
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf)\n"
        "0.0,0.0\n"
        "0.1,200.0\n"
    )
