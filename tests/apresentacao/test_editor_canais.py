import pytest

from ensaios_ni.apresentacao.editor_canais import EditorDeCanais
from ensaios_ni.dominio.erros import ConfiguracaoInvalida


def _perfil_com_dois_canais(tmp_path):
    arq = tmp_path / "perfil.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
        '\n'
        '[canais."Mod1/ai1"]\n'
        'tipo = "tensao"\n'
        'unidade = "bar"\n'
        'ganho = 25.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )
    return arq


def test_adicionar_canal_persiste_no_perfil(tmp_path):
    arq = tmp_path / "perfil.toml"
    arq.write_text("", encoding="utf-8")
    editor = EditorDeCanais(arq)
    editor.adicionar_canal("Mod1/ai0", {"tipo": "tensao", "unidade": "kgf", "ganho": 100.0, "offset": 0.0})
    assert "Mod1/ai0" in editor.canais()


def test_remover_canal_tira_do_perfil(tmp_path):
    editor = EditorDeCanais(_perfil_com_dois_canais(tmp_path))
    editor.remover_canal("Mod1/ai0")
    canais = editor.canais()
    assert "Mod1/ai0" not in canais
    assert "Mod1/ai1" in canais


def test_adicionar_canal_recusa_tipo_invalido_sem_persistir(tmp_path):
    arq = tmp_path / "perfil.toml"
    arq.write_text("", encoding="utf-8")
    editor = EditorDeCanais(arq)
    with pytest.raises(ConfiguracaoInvalida):
        editor.adicionar_canal("Mod1/ai0", {"tipo": "temperatura", "unidade": "°C"})
    assert len(editor.canais()) == 0  # não gravou lixo no perfil


def test_adicionar_canal_recusa_sem_unidade_sem_persistir(tmp_path):
    arq = tmp_path / "perfil.toml"
    arq.write_text("", encoding="utf-8")
    editor = EditorDeCanais(arq)
    with pytest.raises(ConfiguracaoInvalida):
        editor.adicionar_canal("Mod1/ai0", {"tipo": "tensao", "unidade": ""})
    assert len(editor.canais()) == 0


def test_adicionar_canal_sem_conversao_recusa_sem_persistir(tmp_path):
    # canal de tensão sem ganho/offset nem pontos: o carregar_canais rejeitaria — não pode ser gravado.
    # foi o bug do 'fre': gravava (validação de escrita frouxa) e depois o editor crashava ao reler.
    arq = tmp_path / "perfil.toml"
    arq.write_text("", encoding="utf-8")
    editor = EditorDeCanais(arq)
    with pytest.raises(ConfiguracaoInvalida):
        editor.adicionar_canal("fre", {"tipo": "tensao", "unidade": "kgf"})
    assert len(editor.canais()) == 0  # não deixou o perfil num estado que não relê


def test_linhas_lista_canais_mesmo_com_um_invalido(tmp_path):
    # o editor precisa ABRIR pra corrigir: a listagem tolera um canal inválido em vez de derrubar tudo
    arq = tmp_path / "perfil.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\ntipo = "tensao"\nunidade = "kgf"\nrotulo = "Carga"\nganho = 100.0\noffset = 0.0\n'
        '[canais."fre"]\ntipo = "tensao"\nunidade = "kgf"\n',  # inválido: sem ganho/offset
        encoding="utf-8",
    )
    linhas = EditorDeCanais(arq).linhas()
    assert [linha.nome for linha in linhas] == ["Mod1/ai0", "fre"]  # lista os dois, inclusive o inválido
    assert linhas[0].etiqueta == "Carga"  # exibe o Nome do Sinal quando há rótulo


def test_campos_reabre_um_canal_mesmo_com_outro_invalido_no_perfil(tmp_path):
    # reabrir um canal para editar não pode falhar porque OUTRO canal do perfil está inválido
    # (o tio precisa poder editar/corrigir justamente o canal quebrado)
    arq = tmp_path / "perfil.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\ntipo = "tensao"\nunidade = "kgf"\nrotulo = "Carga"\nganho = 100.0\noffset = 0.0\n'
        '[canais."fre"]\ntipo = "tensao"\nunidade = "kgf"\n',  # inválido: sem ganho/offset
        encoding="utf-8",
    )
    editor = EditorDeCanais(arq)
    assert editor.campos("Mod1/ai0") == {
        "tipo": "tensao", "unidade": "kgf", "rotulo": "Carga", "ganho": 100.0, "offset": 0.0
    }
    assert editor.campos("fre") == {"tipo": "tensao", "unidade": "kgf"}  # até o inválido reabre
