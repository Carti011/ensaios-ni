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
