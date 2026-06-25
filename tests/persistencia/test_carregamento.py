import pytest

from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.csv_ensaio import carregar_csv, gravar_ensaio


def test_round_trip_reconstroi_a_serie(tmp_path):
    caminho = tmp_path / "ensaio.csv"
    gravar_ensaio(
        caminho,
        amostras_por_canal={"Mod1/ai0": [200.0, 201.0, 202.0], "Mod3/ai0": [10.0, 11.0, 12.0]},
        taxa_hz=100.0,
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
    )

    serie = carregar_csv(caminho)

    assert serie == SerieTemporal(
        canais=["Mod1/ai0", "Mod3/ai0"],
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
        taxa_hz=100.0,
        dados={"Mod1/ai0": [200.0, 201.0, 202.0], "Mod3/ai0": [10.0, 11.0, 12.0]},
    )


def test_carrega_cabecalho_sem_unidade(tmp_path):
    caminho = tmp_path / "ensaio.csv"
    gravar_ensaio(
        caminho,
        amostras_por_canal={"Mod1/ai0": [1.0, 2.0]},
        taxa_hz=50.0,
    )

    serie = carregar_csv(caminho)

    assert serie.canais == ["Mod1/ai0"]
    assert serie.unidades == {}
    assert serie.taxa_hz == 50.0
    assert serie.dados == {"Mod1/ai0": [1.0, 2.0]}


def test_recusa_csv_com_uma_unica_amostra(tmp_path):
    caminho = tmp_path / "ensaio.csv"
    gravar_ensaio(
        caminho,
        amostras_por_canal={"Mod1/ai0": [1.0]},
        taxa_hz=50.0,
    )

    with pytest.raises(ValueError, match="taxa de amostragem"):
        carregar_csv(caminho)
