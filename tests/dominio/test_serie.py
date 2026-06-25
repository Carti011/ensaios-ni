import pytest

from ensaios_ni.dominio.serie import SerieTemporal


def test_expoe_canais_unidades_taxa_e_dados():
    serie = SerieTemporal(
        canais=["Mod1/ai0", "Mod3/ai0"],
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
        taxa_hz=100.0,
        dados={"Mod1/ai0": [200.0, 201.0], "Mod3/ai0": [10.0, 11.0]},
    )

    assert serie.canais == ["Mod1/ai0", "Mod3/ai0"]
    assert serie.unidades == {"Mod1/ai0": "kgf", "Mod3/ai0": "ue"}
    assert serie.taxa_hz == 100.0
    assert serie.dados == {"Mod1/ai0": [200.0, 201.0], "Mod3/ai0": [10.0, 11.0]}


def test_recusa_taxa_nao_positiva():
    with pytest.raises(ValueError, match="taxa_hz"):
        SerieTemporal(
            canais=["Mod1/ai0"],
            unidades={"Mod1/ai0": "kgf"},
            taxa_hz=0.0,
            dados={"Mod1/ai0": [1.0]},
        )


def test_recusa_canais_com_contagens_diferentes():
    with pytest.raises(ValueError, match="mesmo número de amostras"):
        SerieTemporal(
            canais=["Mod1/ai0", "Mod1/ai1"],
            unidades={},
            taxa_hz=10.0,
            dados={"Mod1/ai0": [1.0, 2.0], "Mod1/ai1": [1.0]},
        )
