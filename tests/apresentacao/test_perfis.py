from pathlib import Path

import pytest

from ensaios_ni.apresentacao.perfis import (
    BibliotecaDePerfis,
    NomeDePerfilInvalido,
    Perfil,
    PerfilJaExiste,
    pasta_padrao,
)
from ensaios_ni.dominio.canais import carregar_canais


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


def test_criar_grava_o_perfil_e_ele_aparece_na_lista(tmp_path):
    biblioteca = BibliotecaDePerfis(tmp_path)
    perfil = biblioteca.criar("ponte-rio-niteroi")
    assert perfil == Perfil(nome="ponte-rio-niteroi", caminho=tmp_path / "ponte-rio-niteroi.toml")
    assert biblioteca.listar() == [perfil]


def test_criar_cria_a_pasta_padrao_se_nao_existe(tmp_path):
    # máquina nova: ~/ensaios-ni ainda não existe — criar não pode quebrar
    biblioteca = BibliotecaDePerfis(tmp_path / "ainda-nao-existe")
    perfil = biblioteca.criar("laje-bloco-b")
    assert perfil.caminho.exists()
    assert biblioteca.listar() == [perfil]


def test_perfil_criado_nasce_carregavel_e_sem_canais(tmp_path):
    # o editor A2 abre no perfil recém-criado: ele precisa carregar sem erro, ainda vazio
    perfil = BibliotecaDePerfis(tmp_path).criar("obra-nova")
    assert len(carregar_canais(perfil.caminho)) == 0


def test_criar_recusa_nome_ja_existente(tmp_path):
    # não sobrescrever um perfil já aferido/configurado
    biblioteca = BibliotecaDePerfis(tmp_path)
    biblioteca.criar("ponte-x")
    with pytest.raises(PerfilJaExiste):
        biblioteca.criar("ponte-x")


@pytest.mark.parametrize("nome", ["", "   "])
def test_criar_recusa_nome_vazio(tmp_path, nome):
    with pytest.raises(NomeDePerfilInvalido):
        BibliotecaDePerfis(tmp_path).criar(nome)


@pytest.mark.parametrize("nome", ["../evil", "sub/dir", "a\\b", ".."])
def test_criar_recusa_nome_com_caractere_de_caminho(tmp_path, nome):
    # segurança: o nome vira nome de arquivo — não pode escapar da pasta de perfis
    with pytest.raises(NomeDePerfilInvalido):
        BibliotecaDePerfis(tmp_path).criar(nome)
