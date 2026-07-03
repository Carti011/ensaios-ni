import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # headless, sem display

from ensaios_ni.apresentacao.editor_canais import EditorDeCanais  # noqa: E402
from ensaios_ni.apresentacao.qt.editor_canais import (  # noqa: E402
    DialogoCanal,
    PainelEditorCanais,
)


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _perfil(tmp_path):
    arq = tmp_path / "perfil.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = "Carga"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )
    return arq


def _perfil_dois(tmp_path):
    arq = tmp_path / "perfil.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = "Carga"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
        '\n'
        '[canais."Mod1/ai1"]\n'
        'tipo = "tensao"\n'
        'unidade = "bar"\n'
        'rotulo = "Pressão"\n'
        'ganho = 25.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )
    return arq


def test_painel_lista_os_canais_do_perfil(app, tmp_path):
    painel = PainelEditorCanais(EditorDeCanais(_perfil(tmp_path)))
    assert painel._tabela.rowCount() == 1
    assert painel._tabela.item(0, 0).text() == "Carga"  # exibe a etiqueta (Nome do Sinal)


def test_remover_o_canal_selecionado_atualiza_a_tabela(app, tmp_path):
    painel = PainelEditorCanais(EditorDeCanais(_perfil_dois(tmp_path)))
    painel._tabela.setCurrentCell(0, 0)  # seleciona "Carga"
    painel._remover_selecionado()
    assert painel._tabela.rowCount() == 1
    assert painel._tabela.item(0, 0).text() == "Pressão"  # sobrou o outro


def test_dialogo_preserva_os_campos_de_um_canal_de_tensao(app):
    entrada = {"tipo": "tensao", "unidade": "kgf", "rotulo": "Carga", "ganho": 100.0, "offset": 0.0}
    nome, campos = DialogoCanal("Mod1/ai0", entrada).campos()
    assert nome == "Mod1/ai0"
    assert campos == entrada


def test_dialogo_inclui_o_gage_factor_quando_strain(app):
    entrada = {"tipo": "strain", "unidade": "µε", "gage_factor": 2.14, "ganho": 1000000.0, "offset": 0.0}
    _nome, campos = DialogoCanal("cDAQ9184-1820306Mod3/ai0", entrada).campos()
    assert campos["gage_factor"] == 2.14
    assert campos["tipo"] == "strain"


def test_aplicar_canal_adiciona_e_atualiza_a_tabela(app, tmp_path):
    arq = tmp_path / "vazio.toml"
    arq.write_text("", encoding="utf-8")
    painel = PainelEditorCanais(EditorDeCanais(arq))
    assert painel._tabela.rowCount() == 0
    painel._aplicar_canal(
        "Mod1/ai0", {"tipo": "tensao", "unidade": "kgf", "rotulo": "Carga", "ganho": 100.0, "offset": 0.0}
    )
    assert painel._tabela.rowCount() == 1
    assert painel._tabela.item(0, 0).text() == "Carga"


def test_campos_do_canal_reflete_o_canal_para_reeditar(app, tmp_path):
    painel = PainelEditorCanais(EditorDeCanais(_perfil(tmp_path)))
    canal = painel._editor.canais()["Mod1/ai0"]
    assert painel._campos_do_canal(canal) == {
        "tipo": "tensao",
        "unidade": "kgf",
        "rotulo": "Carga",
        "ganho": 100.0,
        "offset": 0.0,
    }
