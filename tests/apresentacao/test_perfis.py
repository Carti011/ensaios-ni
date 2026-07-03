from pathlib import Path

from ensaios_ni.apresentacao.perfis import BibliotecaDePerfis, Perfil, pasta_padrao


def test_lista_os_toml_da_pasta_como_perfis(tmp_path):
    (tmp_path / "ponte-rio-niteroi.toml").write_text("", encoding="utf-8")
    perfis = BibliotecaDePerfis(tmp_path).listar()
    assert perfis == [Perfil(nome="ponte-rio-niteroi", caminho=tmp_path / "ponte-rio-niteroi.toml")]


def test_ordena_os_perfis_por_nome(tmp_path):
    for nome in ("zulu", "alfa", "mike"):
        (tmp_path / f"{nome}.toml").write_text("", encoding="utf-8")
    nomes = [perfil.nome for perfil in BibliotecaDePerfis(tmp_path).listar()]
    assert nomes == ["alfa", "mike", "zulu"]


def test_pasta_inexistente_devolve_lista_vazia(tmp_path):
    # a tela inicial não pode quebrar se a pasta-padrão ainda não foi criada
    assert BibliotecaDePerfis(tmp_path / "ainda-nao-existe").listar() == []


def test_ignora_o_que_nao_e_perfil_de_canais(tmp_path):
    (tmp_path / "ponte.toml").write_text("", encoding="utf-8")
    (tmp_path / "ensaio.meta.toml").write_text("", encoding="utf-8")  # metadata de ensaio (ADR-018)
    (tmp_path / "ensaio.csv").write_text("", encoding="utf-8")
    nomes = [perfil.nome for perfil in BibliotecaDePerfis(tmp_path).listar()]
    assert nomes == ["ponte"]  # só o perfil de canais; .meta.toml e .csv de fora


def test_pasta_padrao_fica_sob_o_home_do_usuario():
    assert pasta_padrao() == Path.home() / "ensaios-ni"
