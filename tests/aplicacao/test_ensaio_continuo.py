from ensaios_ni.aplicacao.ensaio import executar_ensaio_continuo
from ensaios_ni.aquisicao.fake import AquisicaoFake
from ensaios_ni.dominio.canais import Canais, Canal


def test_continuo_grava_blocos_de_tensao_com_tempo_continuo(tmp_path):
    # 4 amostras emitidas em 2 blocos de 2; o tempo segue contínuo entre os blocos
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    canais = Canais({"Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0)})
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio_continuo(
        fonte, canais, taxa_hz=10.0, caminho=caminho, amostras_por_bloco=2
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf)\n"
        "0.0,100.0\n"
        "0.1,200.0\n"
        "0.2,300.0\n"
        "0.3,400.0\n"
    )


def test_continuo_costura_tensao_e_strain_bloco_a_bloco(tmp_path):
    fonte = AquisicaoFake(
        tensoes={"Mod1/ai0": [2.0, 2.5]},
        strains={"Mod3/ai0": [1e-4, 2e-4]},
    )
    canais = Canais({
        "Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0),
        "Mod3/ai0": Canal("Mod3/ai0", "strain", "µε", 1_000_000.0, 0.0),
    })
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio_continuo(
        fonte, canais, taxa_hz=10.0, caminho=caminho, amostras_por_bloco=1
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf),Mod3/ai0 (µε)\n"
        "0.0,200.0,100.0\n"
        "0.1,250.0,200.0\n"
    )


def test_continuo_aplica_tara_capturada_no_repouso(tmp_path):
    # tara: lê repouso (finito) das duas tasks antes de transmitir, subtrai de tudo
    fonte = AquisicaoFake(
        tensoes={"Mod1/ai0": [1.0, 3.0]},
        strains={"Mod3/ai0": [1e-4, 5e-4]},
    )
    canais = Canais({
        "Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0),
        "Mod3/ai0": Canal("Mod3/ai0", "strain", "µε", 1_000_000.0, 0.0),
    })
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio_continuo(
        fonte, canais, taxa_hz=10.0, caminho=caminho,
        amostras_por_bloco=1, amostras_tara=1,
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf),Mod3/ai0 (µε)\n"
        "0.0,0.0,0.0\n"
        "0.1,200.0,400.0\n"
    )


def test_continuo_para_apos_a_duracao_pedida(tmp_path):
    # o fluxo tem 5 amostras, mas a duração de 0,2 s a 10 Hz cobre só 2
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0, 5.0]})
    canais = Canais({"Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0)})
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio_continuo(
        fonte, canais, taxa_hz=10.0, caminho=caminho,
        amostras_por_bloco=1, duracao_s=0.2,
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf)\n"
        "0.0,100.0\n"
        "0.1,200.0\n"
    )


def test_continuo_encerra_limpo_quando_parar_dispara(tmp_path):
    # parar() (ligado ao Ctrl-C na CLI) encerra após gravar o bloco corrente
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    canais = Canais({"Mod1/ai0": Canal("Mod1/ai0", "tensao", "kgf", 100.0, 0.0)})
    caminho = tmp_path / "ensaio.csv"

    executar_ensaio_continuo(
        fonte, canais, taxa_hz=10.0, caminho=caminho,
        amostras_por_bloco=1, parar=lambda: True,
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf)\n"
        "0.0,100.0\n"
    )
