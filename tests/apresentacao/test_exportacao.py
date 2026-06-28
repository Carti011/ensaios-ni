from ensaios_ni.apresentacao.exportacao import Exportacao
from ensaios_ni.persistencia.csv_ensaio import gravar_ensaio


def _csv_de_ensaio(caminho):
    gravar_ensaio(
        caminho,
        {"Mod1/ai0": [200.0, 201.5], "Mod3/ai0": [10.0, 11.25]},
        taxa_hz=50.0,
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "µε"},
    )


def test_exporta_o_csv_gravado_no_formato_escolhido(tmp_path):
    origem = tmp_path / "ensaio.csv"
    _csv_de_ensaio(origem)
    exp = Exportacao(origem)
    destino = tmp_path / "saida.csv"
    exp.exportar("csv-excel-br", destino)
    assert destino.exists()
    assert ";" in destino.read_text(encoding="utf-8-sig")  # csv-excel-br: separador ;


def test_sinais_lista_os_canais_do_ensaio(tmp_path):
    origem = tmp_path / "ensaio.csv"
    _csv_de_ensaio(origem)
    assert Exportacao(origem).sinais() == ["Mod1/ai0", "Mod3/ai0"]


def test_exporta_so_os_sinais_e_a_janela_escolhidos(tmp_path):
    origem = tmp_path / "ensaio.csv"
    gravar_ensaio(
        origem,
        {"Mod1/ai0": [200.0, 201.5, 202.0], "Mod3/ai0": [10.0, 11.25, 12.0]},
        taxa_hz=50.0,
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "µε"},
    )
    destino = tmp_path / "saida.csv"
    Exportacao(origem).exportar("csv-excel-br", destino, sinais=["Mod1/ai0"], inicio_s=0.0, fim_s=0.02)
    conteudo = destino.read_text(encoding="utf-8-sig")
    assert "Mod1/ai0 (kgf)" in conteudo and "Mod3/ai0" not in conteudo  # só o sinal escolhido
    assert "0,04" not in conteudo  # janela [0; 0,02] descarta a 3ª amostra (0,04 s)
