import pytest

from ensaios_ni.__main__ import _parse_args, main
from ensaios_ni.persistencia.csv_ensaio import gravar_ensaio


def test_main_modo_fake_gera_csv(tmp_path):
    saida = tmp_path / "ensaio.csv"
    main(["--fonte", "fake", "--amostras", "10", "--taxa", "50", "--saida", str(saida)])
    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert linhas[0].startswith("tempo_s,")
    assert len(linhas) == 11  # cabeçalho + 10 amostras


def test_main_aceita_config_explicita(tmp_path):
    config = tmp_path / "canais.toml"
    config.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\nunidade = "kgf"\nganho = 100.0\noffset = 0.0\n',
        encoding="utf-8",
    )
    saida = tmp_path / "ensaio.csv"
    main([
        "--fonte", "fake", "--config", str(config),
        "--amostras", "5", "--taxa", "20", "--saida", str(saida),
    ])
    assert saida.read_text(encoding="utf-8").splitlines()[0] == "tempo_s,Mod1/ai0 (kgf)"


def test_cli_aceita_amostras_tara():
    args = _parse_args(["--fonte", "daqmx", "--config", "x.toml", "--amostras-tara", "200"])
    assert args.amostras_tara == 200


def test_cli_amostras_tara_default_zero():
    args = _parse_args(["--fonte", "fake"])
    assert args.amostras_tara == 0


def test_cli_modo_continuo_aceita_duracao_e_bloco():
    args = _parse_args(["--continuo", "--duracao-s", "5", "--bloco", "256"])
    assert args.continuo is True
    assert args.duracao_s == 5.0
    assert args.bloco == 256


def test_main_continuo_fake_grava_pela_duracao(tmp_path):
    saida = tmp_path / "ensaio.csv"
    main([
        "--continuo", "--fonte", "fake", "--taxa", "10", "--bloco", "5",
        "--duracao-s", "1", "--saida", str(saida),
    ])
    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert linhas[0].startswith("tempo_s,")
    assert len(linhas) == 11  # 1 s a 10 Hz = 10 amostras + cabeçalho


def test_cli_exporta_csv_para_excel_br(tmp_path):
    origem = tmp_path / "ensaio.csv"
    gravar_ensaio(origem, {"Mod1/ai0": [200.0, 201.5]}, taxa_hz=50.0, unidades={"Mod1/ai0": "kgf"})
    destino = tmp_path / "saida.csv"

    main(["--exportar", "csv-excel-br", "--de", str(origem), "--saida", str(destino)])

    conteudo = destino.read_text(encoding="utf-8-sig").splitlines()
    assert conteudo[0] == "tempo_s;Mod1/ai0 (kgf)"
    assert conteudo[1] == "0,0;200,0"


def test_cli_exporta_xlsx(tmp_path):
    import openpyxl

    origem = tmp_path / "ensaio.csv"
    gravar_ensaio(origem, {"Mod1/ai0": [200.0, 201.5]}, taxa_hz=50.0, unidades={"Mod1/ai0": "kgf"})
    destino = tmp_path / "saida.xlsx"

    main(["--exportar", "xlsx", "--de", str(origem), "--saida", str(destino)])

    aba = openpyxl.load_workbook(destino).active
    assert list(aba.iter_rows(values_only=True))[0] == ("tempo_s", "Mod1/ai0 (kgf)")


def test_cli_exporta_apenas_sinais_selecionados(tmp_path):
    origem = tmp_path / "ensaio.csv"
    gravar_ensaio(
        origem,
        {"Mod1/ai0": [200.0, 201.0], "Mod3/ai0": [10.0, 11.0]},
        taxa_hz=50.0,
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "ue"},
    )
    destino = tmp_path / "saida.csv"

    main([
        "--exportar", "csv-excel-br", "--de", str(origem),
        "--saida", str(destino), "--sinais", "Mod1/ai0",
    ])

    conteudo = destino.read_text(encoding="utf-8-sig").splitlines()
    assert conteudo[0] == "tempo_s;Mod1/ai0 (kgf)"
    assert conteudo[1] == "0,0;200,0"


def test_cli_exportar_exige_de():
    with pytest.raises(SystemExit, match="--de"):
        main(["--exportar", "xlsx", "--saida", "x.xlsx"])
