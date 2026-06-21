import pytest

from ensaios_ni.persistencia.csv_ensaio import gravar_ensaio


def test_grava_um_canal_com_coluna_de_tempo(tmp_path):
    caminho = tmp_path / "ensaio.csv"

    gravar_ensaio(
        caminho,
        amostras_por_canal={"Mod1/ai0": [200.0, 201.0, 202.0]},
        taxa_hz=100.0,
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0\n"
        "0.0,200.0\n"
        "0.01,201.0\n"
        "0.02,202.0\n"
    )


def test_grava_multiplos_canais_alinhados_pelo_tempo(tmp_path):
    caminho = tmp_path / "ensaio.csv"

    gravar_ensaio(
        caminho,
        amostras_por_canal={"Mod1/ai0": [200.0, 201.0], "Mod1/ai1": [10.0, 11.0]},
        taxa_hz=50.0,
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0,Mod1/ai1\n"
        "0.0,200.0,10.0\n"
        "0.02,201.0,11.0\n"
    )


def test_recusa_canais_com_contagens_diferentes(tmp_path):
    caminho = tmp_path / "ensaio.csv"

    with pytest.raises(ValueError, match="mesmo número de amostras"):
        gravar_ensaio(
            caminho,
            amostras_por_canal={"Mod1/ai0": [1.0, 2.0], "Mod1/ai1": [1.0]},
            taxa_hz=10.0,
        )


def test_grava_unidade_no_cabecalho_quando_informada(tmp_path):
    caminho = tmp_path / "ensaio.csv"

    gravar_ensaio(
        caminho,
        amostras_por_canal={"Mod1/ai0": [200.0], "Mod1/ai1": [3.5]},
        taxa_hz=10.0,
        unidades={"Mod1/ai0": "kgf", "Mod1/ai1": "bar"},
    )

    assert caminho.read_text(encoding="utf-8") == (
        "tempo_s,Mod1/ai0 (kgf),Mod1/ai1 (bar)\n"
        "0.0,200.0,3.5\n"
    )


def test_recusa_taxa_nao_positiva(tmp_path):
    caminho = tmp_path / "ensaio.csv"

    with pytest.raises(ValueError, match="taxa_hz"):
        gravar_ensaio(
            caminho,
            amostras_por_canal={"Mod1/ai0": [1.0, 2.0]},
            taxa_hz=0.0,
        )
