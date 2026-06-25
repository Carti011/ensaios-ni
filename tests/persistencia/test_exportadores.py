import pytest

from ensaios_ni.dominio.serie import SerieTemporal
from ensaios_ni.persistencia.exportadores import exportar_csv_excel_br, exportar_xlsx


def test_csv_excel_br_usa_ponto_e_virgula_e_decimal_virgula(tmp_path):
    caminho = tmp_path / "ensaio.csv"
    serie = SerieTemporal(
        canais=["Mod1/ai0", "Mod3/ai0"],
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
        taxa_hz=50.0,
        dados={"Mod1/ai0": [200.0, 201.5], "Mod3/ai0": [10.0, 11.25]},
    )

    exportar_csv_excel_br(serie, caminho)

    assert caminho.read_text(encoding="utf-8-sig") == (
        "tempo_s;Mod1/ai0 (kgf);Mod3/ai0 (ue)\n"
        "0,0;200,0;10,0\n"
        "0,02;201,5;11,25\n"
    )


def test_csv_excel_br_seleciona_sinais_na_ordem_da_serie(tmp_path):
    caminho = tmp_path / "ensaio.csv"
    serie = SerieTemporal(
        canais=["Mod1/ai0", "Mod1/ai1", "Mod3/ai0"],
        unidades={"Mod1/ai0": "kgf", "Mod1/ai1": "bar", "Mod3/ai0": "ue"},
        taxa_hz=50.0,
        dados={"Mod1/ai0": [200.0], "Mod1/ai1": [3.0], "Mod3/ai0": [10.0]},
    )

    exportar_csv_excel_br(serie, caminho, sinais=["Mod3/ai0", "Mod1/ai0"])

    assert caminho.read_text(encoding="utf-8-sig") == (
        "tempo_s;Mod1/ai0 (kgf);Mod3/ai0 (ue)\n"
        "0,0;200,0;10,0\n"
    )


def test_csv_excel_br_recusa_sinal_inexistente(tmp_path):
    caminho = tmp_path / "ensaio.csv"
    serie = SerieTemporal(
        canais=["Mod1/ai0"],
        unidades={"Mod1/ai0": "kgf"},
        taxa_hz=50.0,
        dados={"Mod1/ai0": [200.0]},
    )

    with pytest.raises(ValueError, match="inexistentes"):
        exportar_csv_excel_br(serie, caminho, sinais=["Mod9/ai9"])


def test_xlsx_grava_cabecalho_e_numeros_nativos(tmp_path):
    import openpyxl

    caminho = tmp_path / "ensaio.xlsx"
    serie = SerieTemporal(
        canais=["Mod1/ai0", "Mod3/ai0"],
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
        taxa_hz=50.0,
        dados={"Mod1/ai0": [200.0, 201.5], "Mod3/ai0": [10.0, 11.25]},
    )

    exportar_xlsx(serie, caminho)

    planilha = openpyxl.load_workbook(caminho).active
    linhas = list(planilha.iter_rows(values_only=True))
    assert linhas == [
        ("tempo_s", "Mod1/ai0 (kgf)", "Mod3/ai0 (ue)"),
        (0.0, 200.0, 10.0),
        (0.02, 201.5, 11.25),
    ]


def test_xlsx_seleciona_sinais(tmp_path):
    import openpyxl

    caminho = tmp_path / "ensaio.xlsx"
    serie = SerieTemporal(
        canais=["Mod1/ai0", "Mod3/ai0"],
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
        taxa_hz=50.0,
        dados={"Mod1/ai0": [200.0], "Mod3/ai0": [10.0]},
    )

    exportar_xlsx(serie, caminho, sinais=["Mod1/ai0"])

    planilha = openpyxl.load_workbook(caminho).active
    linhas = list(planilha.iter_rows(values_only=True))
    assert linhas == [
        ("tempo_s", "Mod1/ai0 (kgf)"),
        (0.0, 200.0),
    ]
