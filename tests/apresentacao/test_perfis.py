from pathlib import Path

import pytest

from ensaios_ni.apresentacao.perfis import (
    BibliotecaDePerfis,
    ImportacaoInvalida,
    NomeDePerfilInvalido,
    Perfil,
    PerfilJaExiste,
    PerfilNaoExiste,
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


def _toml_de_um_canal(caminho: Path) -> Path:
    caminho.write_text(
        '[canais."Mod1/ai0"]\ntipo = "tensao"\nunidade = "kgf"\nganho = 1.0\noffset = 0.0\n',
        encoding="utf-8",
    )
    return caminho


def test_importar_copia_o_toml_avulso_para_a_biblioteca(tmp_path):
    # o tio recebeu um .toml de fora e quer geri-lo pela tela: importar o adota na biblioteca
    origem = _toml_de_um_canal(tmp_path / "ponte-x.toml")
    biblioteca = BibliotecaDePerfis(tmp_path / "biblioteca")
    perfil = biblioteca.importar(origem)
    assert perfil == Perfil(nome="ponte-x", caminho=tmp_path / "biblioteca" / "ponte-x.toml")
    assert biblioteca.listar() == [perfil]
    assert len(carregar_canais(perfil.caminho)) == 1  # conteúdo preservado


def test_importar_recusa_nome_ja_existente(tmp_path):
    # não sobrescrever um perfil já na biblioteca
    origem = _toml_de_um_canal(tmp_path / "ponte-x.toml")
    biblioteca = BibliotecaDePerfis(tmp_path / "biblioteca")
    biblioteca.importar(origem)
    with pytest.raises(PerfilJaExiste):
        biblioteca.importar(origem)


def test_importar_recusa_origem_inexistente(tmp_path):
    biblioteca = BibliotecaDePerfis(tmp_path / "biblioteca")
    with pytest.raises(ImportacaoInvalida):
        biblioteca.importar(tmp_path / "nao-existe.toml")


def test_importar_recusa_toml_invalido_sem_deixar_lixo(tmp_path):
    # canal sem 'tipo' -> ConfiguracaoInvalida; a biblioteca não pode adotar config quebrado
    origem = tmp_path / "quebrado.toml"
    origem.write_text('[canais."Mod1/ai0"]\nunidade = "kgf"\n', encoding="utf-8")
    biblioteca = BibliotecaDePerfis(tmp_path / "biblioteca")
    with pytest.raises(ImportacaoInvalida):
        biblioteca.importar(origem)
    assert biblioteca.listar() == []  # nada entrou na biblioteca


def test_importar_com_nome_customizado_valida_o_nome(tmp_path):
    # o nome de destino (quando informado) passa pela mesma validação do criar
    origem = _toml_de_um_canal(tmp_path / "ponte-x.toml")
    biblioteca = BibliotecaDePerfis(tmp_path / "biblioteca")
    with pytest.raises(NomeDePerfilInvalido):
        biblioteca.importar(origem, nome="../evil")


def test_remover_apaga_o_perfil_e_ele_some_da_lista(tmp_path):
    biblioteca = BibliotecaDePerfis(tmp_path)
    biblioteca.criar("ponte-x")
    biblioteca.criar("laje-y")
    biblioteca.remover("ponte-x")
    assert [p.nome for p in biblioteca.listar()] == ["laje-y"]
    assert not (tmp_path / "ponte-x.toml").exists()


def test_remover_recusa_perfil_inexistente(tmp_path):
    with pytest.raises(PerfilNaoExiste):
        BibliotecaDePerfis(tmp_path).remover("fantasma")


def test_renomear_move_o_perfil_preservando_o_conteudo(tmp_path):
    _toml_de_um_canal(tmp_path / "ponte-x.toml")  # perfil com 1 canal
    biblioteca = BibliotecaDePerfis(tmp_path)
    perfil = biblioteca.renomear("ponte-x", "ponte-rio-niteroi")
    assert perfil == Perfil(nome="ponte-rio-niteroi", caminho=tmp_path / "ponte-rio-niteroi.toml")
    assert [p.nome for p in biblioteca.listar()] == ["ponte-rio-niteroi"]
    assert not (tmp_path / "ponte-x.toml").exists()
    assert len(carregar_canais(perfil.caminho)) == 1  # conteúdo preservado


def test_renomear_recusa_novo_nome_ja_existente(tmp_path):
    biblioteca = BibliotecaDePerfis(tmp_path)
    biblioteca.criar("ponte-x")
    biblioteca.criar("laje-y")
    with pytest.raises(PerfilJaExiste):
        biblioteca.renomear("ponte-x", "laje-y")


@pytest.mark.parametrize("novo", ["", "../evil", "sub/dir"])
def test_renomear_valida_o_novo_nome(tmp_path, novo):
    BibliotecaDePerfis(tmp_path).criar("ponte-x")
    with pytest.raises(NomeDePerfilInvalido):
        BibliotecaDePerfis(tmp_path).renomear("ponte-x", novo)


def test_renomear_recusa_atual_inexistente(tmp_path):
    with pytest.raises(PerfilNaoExiste):
        BibliotecaDePerfis(tmp_path).renomear("fantasma", "novo-nome")


def test_duplicar_copia_o_perfil_com_novo_nome(tmp_path):
    _toml_de_um_canal(tmp_path / "ponte-x.toml")  # perfil com 1 canal
    biblioteca = BibliotecaDePerfis(tmp_path)
    perfil = biblioteca.duplicar("ponte-x", "ponte-x-copia")
    assert [p.nome for p in biblioteca.listar()] == ["ponte-x", "ponte-x-copia"]
    assert len(carregar_canais(perfil.caminho)) == 1  # conteúdo preservado
    assert (tmp_path / "ponte-x.toml").exists()  # o original fica intacto


def test_duplicar_recusa_origem_inexistente(tmp_path):
    with pytest.raises(PerfilNaoExiste):
        BibliotecaDePerfis(tmp_path).duplicar("fantasma", "copia")


def test_duplicar_recusa_novo_nome_ja_existente(tmp_path):
    biblioteca = BibliotecaDePerfis(tmp_path)
    biblioteca.criar("ponte-x")
    biblioteca.criar("laje-y")
    with pytest.raises(PerfilJaExiste):
        biblioteca.duplicar("ponte-x", "laje-y")


def test_exportar_copia_o_perfil_para_caminho_externo(tmp_path):
    # o tio "envia o config da Ponte X": exporta o perfil para um arquivo fora da biblioteca
    pasta = tmp_path / "biblioteca"
    pasta.mkdir()
    _toml_de_um_canal(pasta / "ponte-x.toml")
    destino = tmp_path / "config-para-enviar.toml"
    resultado = BibliotecaDePerfis(pasta).exportar("ponte-x", destino)
    assert resultado == destino
    assert len(carregar_canais(destino)) == 1  # conteúdo copiado
    assert (pasta / "ponte-x.toml").exists()  # o perfil na biblioteca fica intacto


def test_exportar_recusa_perfil_inexistente(tmp_path):
    with pytest.raises(PerfilNaoExiste):
        BibliotecaDePerfis(tmp_path).exportar("fantasma", tmp_path / "saida.toml")
