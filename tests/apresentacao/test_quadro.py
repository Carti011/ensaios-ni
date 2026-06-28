import pytest

from ensaios_ni.apresentacao.monitor import QuadroAoVivo


def test_agrupar_por_unidade_separa_unidades_distintas():
    quadro = QuadroAoVivo(
        tempos=[0.0, 0.25],
        dados={"Mod1/ai0": [10.0, 20.0], "Mod3/ai0": [1000.0, 1000.0]},
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "µε"},
    )

    grupos = quadro.agrupar_por_unidade()

    assert [grupo.unidade for grupo in grupos] == ["kgf", "µε"]
    assert grupos[0].dados == {"Mod1/ai0": [10.0, 20.0]}
    assert grupos[1].dados == {"Mod3/ai0": [1000.0, 1000.0]}


def test_agrupar_por_unidade_junta_canais_de_mesma_unidade_na_ordem_do_config():
    quadro = QuadroAoVivo(
        tempos=[0.0],
        dados={
            "Mod1/ai0": [10.0],
            "Mod2/ai0": [50.0],
            "Mod2/ai1": [90.0],
            "Mod3/ai0": [1000.0],
        },
        unidades={
            "Mod1/ai0": "kgf",
            "Mod2/ai0": "mm",
            "Mod2/ai1": "mm",
            "Mod3/ai0": "µε",
        },
    )

    grupos = quadro.agrupar_por_unidade()

    assert [grupo.unidade for grupo in grupos] == ["kgf", "mm", "µε"]
    assert list(grupos[1].dados.keys()) == ["Mod2/ai0", "Mod2/ai1"]
    assert grupos[1].dados == {"Mod2/ai0": [50.0], "Mod2/ai1": [90.0]}


def test_agrupar_por_unidade_sem_dados_devolve_lista_vazia():
    quadro = QuadroAoVivo(tempos=[], dados={}, unidades={})

    assert quadro.agrupar_por_unidade() == []


def test_par_xy_pareia_carga_e_deformacao_ponto_a_ponto():
    quadro = QuadroAoVivo(
        tempos=[0.0, 0.25, 0.5],
        dados={"Mod1/ai0": [10.0, 20.0, 30.0], "Mod3/ai0": [100.0, 200.0, 300.0]},
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "µε"},
    )

    par = quadro.par_xy("Mod1/ai0", "Mod3/ai0")

    assert par.canal_x == "Mod1/ai0"
    assert par.canal_y == "Mod3/ai0"
    assert par.xs == [10.0, 20.0, 30.0]
    assert par.ys == [100.0, 200.0, 300.0]
