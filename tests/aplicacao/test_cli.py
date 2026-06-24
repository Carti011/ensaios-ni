from ensaios_ni.__main__ import _parse_args, main


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
