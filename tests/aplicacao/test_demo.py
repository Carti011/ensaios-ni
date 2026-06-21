from ensaios_ni.aplicacao.demo import executar_demonstracao


def test_demonstracao_gera_csv_com_cabecalho_e_uma_linha_por_amostra(tmp_path):
    caminho = tmp_path / "demo.csv"

    resultado = executar_demonstracao(caminho, amostras=50, taxa_hz=100.0)

    assert resultado == caminho
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert linhas[0] == "tempo_s,Mod1/ai0 (kgf),Mod1/ai1 (bar)"
    assert len(linhas) == 51  # cabeçalho + 50 amostras
