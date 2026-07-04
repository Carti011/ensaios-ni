import os
from pathlib import Path

import pytest

# o launcher abre a JanelaMonitor (PySide) ligada ao AdaptadorDaqmx; sem o extra [gui], pula
pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # roda headless, sem display

from ensaios_ni.apresentacao.qt.hardware import (  # noqa: E402
    TelaInicial,
    _parse_args,
    _widget_de,
    main,
    montar_janela,
)
from ensaios_ni.apresentacao.qt.janela import JanelaMonitor  # noqa: E402
from ensaios_ni.aquisicao.daqmx import AdaptadorDaqmx  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _config(tmp_path):
    arq = tmp_path / "canais.toml"
    arq.write_text(
        '[canais."cDAQ9184-1820306Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = "Carga"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
        '\n'
        '[canais."cDAQ9184-1820306Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'rotulo = "Sg1 bico"\n'
        'gage_factor = 2.14\n'
        'ganho = 1000000.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )
    return arq


def test_montar_janela_liga_o_dashboard_ao_hardware_real(app, tmp_path):
    # o launcher monta a cadeia real: canais do TOML -> AdaptadorDaqmx -> monitor -> janela
    janela = montar_janela(
        _config(tmp_path), taxa_hz=1024.0, bloco=256, saida=tmp_path / "ensaio.csv"
    )
    assert isinstance(janela, JanelaMonitor)
    assert isinstance(janela._monitor._fonte, AdaptadorDaqmx)


def test_montar_janela_repassa_canais_e_config_para_aferir_e_rotular(app, tmp_path):
    # o gap que o abrir(monitor) da demo não cobre: com hardware real, Aferir e os
    # rótulos (Nome do Sinal) precisam funcionar — exigem canais + caminho de config
    janela = montar_janela(
        _config(tmp_path), taxa_hz=1024.0, bloco=256, saida=tmp_path / "ensaio.csv"
    )
    assert janela._btn_aferir.isEnabled() is True  # há config: aferição habilitada
    assert janela._tabela.item(0, 0).text() == "Carga"  # exibe o rótulo, não o endereço


def test_tela_inicial_abre_o_dashboard_a_partir_do_config(app, tmp_path):
    # o tio clica em "Abrir configuração", escolhe o toml e o dashboard monta com os canais
    tela = TelaInicial(saida=tmp_path / "ensaio.csv")
    janela = tela.abrir_config(_config(tmp_path))
    assert isinstance(janela, JanelaMonitor)
    assert isinstance(janela._monitor._fonte, AdaptadorDaqmx)
    assert janela._tabela.item(0, 0).text() == "Carga"


def test_tela_inicial_lista_os_perfis_salvos(app, tmp_path):
    # a tela mostra os ensaios salvos na pasta de perfis, para o tio escolher sem abrir arquivo
    (tmp_path / "ponte-x.toml").write_text("", encoding="utf-8")
    (tmp_path / "laje-y.toml").write_text("", encoding="utf-8")
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path)
    nomes = [tela._lista_perfis.item(i).text() for i in range(tela._lista_perfis.count())]
    assert nomes == ["laje-y", "ponte-x"]  # ordenados por nome


def test_tela_inicial_abre_o_perfil_escolhido(app, tmp_path):
    # escolher um perfil da lista monta o dashboard, reusando o abrir_config
    _config(tmp_path)  # cria canais.toml (válido) na pasta de perfis
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path)
    tela._lista_perfis.setCurrentRow(0)
    janela = tela._abrir_perfil(tela._lista_perfis.currentItem())
    assert isinstance(janela, JanelaMonitor)
    assert janela._tabela.item(0, 0).text() == "Carga"  # abriu o config certo


def test_tela_inicial_edita_os_canais_do_perfil_selecionado(app, tmp_path):
    # o tio seleciona um ensaio e edita a tabela de canais sem abrir arquivo (ADR-023 A2)
    from ensaios_ni.apresentacao.qt.editor_canais import PainelEditorCanais

    _config(tmp_path)  # perfil com 2 canais
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path)
    tela._lista_perfis.setCurrentRow(0)
    painel = tela._editar_canais_do_selecionado()
    assert isinstance(painel, PainelEditorCanais)
    assert painel._tabela.rowCount() == 2


def test_editar_canais_desabilitado_sem_selecao(app, tmp_path):
    # o botão não pode ficar clicável-mas-inerte (bug de UX visto no Windows): sem perfil
    # selecionado, fica desabilitado; ao selecionar, habilita
    _config(tmp_path)  # 1 perfil na pasta
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path)
    assert tela._btn_editar.isEnabled() is False
    tela._lista_perfis.setCurrentRow(0)
    assert tela._btn_editar.isEnabled() is True


def test_tela_inicial_cria_ensaio_novo_e_abre_o_editor(app, tmp_path):
    # o tio cria um ensaio pela tela (sem tocar em arquivo) e cai direto no editor de canais
    from ensaios_ni.apresentacao.qt.editor_canais import PainelEditorCanais

    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path)
    painel = tela._criar_perfil("obra-nova")
    assert isinstance(painel, PainelEditorCanais)  # abre o editor A2 no perfil novo
    assert (tmp_path / "obra-nova.toml").exists()  # persistiu o perfil
    nomes = [tela._lista_perfis.item(i).text() for i in range(tela._lista_perfis.count())]
    assert nomes == ["obra-nova"]  # apareceu na lista


def test_tela_inicial_ensaio_duplicado_avisa_na_tela_sem_abrir(app, tmp_path):
    # criar com nome que já existe não pode dar traceback: vira aviso na própria tela
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path)
    tela._criar_perfil("obra")
    painel = tela._criar_perfil("obra")  # nome repetido
    assert painel is None
    assert "já existe" in tela._lbl_erro.text()


def test_tela_inicial_importa_toml_avulso_para_a_biblioteca(app, tmp_path):
    # o tio traz um .toml de fora; importar o adota na biblioteca e ele passa a aparecer na lista
    origem = _config(tmp_path)  # canais.toml válido, fora da biblioteca
    pasta = tmp_path / "biblioteca"
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=pasta)
    perfil = tela._importar_perfil(origem)
    assert perfil is not None
    nomes = [tela._lista_perfis.item(i).text() for i in range(tela._lista_perfis.count())]
    assert "canais" in nomes  # adotado na biblioteca
    assert (pasta / "canais.toml").exists()


def test_tela_inicial_importar_invalido_avisa_na_tela(app, tmp_path):
    # importar config quebrado não pode dar traceback nem sujar a biblioteca
    origem = tmp_path / "quebrado.toml"
    origem.write_text('[canais."Mod1/ai0"]\nunidade = "kgf"\n', encoding="utf-8")  # sem 'tipo'
    tela = TelaInicial(saida=tmp_path / "e.csv", pasta_perfis=tmp_path / "biblioteca")
    perfil = tela._importar_perfil(origem)
    assert perfil is None
    assert "inválido" in tela._lbl_erro.text()


def test_tela_inicial_config_invalido_mostra_erro_sem_abrir(app, tmp_path):
    arq = tmp_path / "canais.toml"  # canal sem 'tipo'
    arq.write_text('[canais."Mod1/ai0"]\nunidade = "kgf"\n', encoding="utf-8")
    tela = TelaInicial(saida=tmp_path / "e.csv")
    janela = tela.abrir_config(arq)
    assert janela is None  # não entra no dashboard com config quebrado
    assert "config inválido" in tela._lbl_erro.text()  # avisa na própria tela


def test_config_inexistente_encerra_com_mensagem_amigavel(app, tmp_path):
    # o tio não pode ver um traceback do Python: config ausente vira mensagem limpa
    with pytest.raises(SystemExit) as saida:
        main(["--config", str(tmp_path / "nao-existe.toml")])
    assert "nao-existe.toml" in str(saida.value)
    assert "Traceback" not in str(saida.value)


def test_config_invalido_encerra_com_mensagem_amigavel(app, tmp_path):
    arq = tmp_path / "canais.toml"  # canal sem 'tipo': ConfiguracaoInvalida
    arq.write_text('[canais."Mod1/ai0"]\nunidade = "kgf"\n', encoding="utf-8")
    with pytest.raises(SystemExit) as saida:
        main(["--config", str(arq)])
    assert "config inválido" in str(saida.value)


def test_toml_quebrado_encerra_com_mensagem_amigavel(app, tmp_path):
    arq = tmp_path / "canais.toml"  # sintaxe TOML inválida (editado à mão pelo tio)
    arq.write_text('[canais."Mod1/ai0"\ntipo = "tensao"\n', encoding="utf-8")
    with pytest.raises(SystemExit) as saida:
        main(["--config", str(arq)])
    assert "config inválido" in str(saida.value)
    assert "Traceback" not in str(saida.value)


def test_entrypoint_cria_qapplication_antes_do_widget():
    # regressão: o QApplication tem que existir antes do primeiro QWidget, senão aborta (SIGABRT).
    # roda num processo NOVO (sem a fixture `app`) — é o único jeito de reproduzir o entrypoint real.
    import subprocess
    import sys

    import ensaios_ni

    src = str(Path(ensaios_ni.__file__).resolve().parents[1])
    codigo = (
        "from ensaios_ni.apresentacao.qt.hardware import _preparar\n"
        "app, w = _preparar([])\n"
        "print(type(w).__name__)\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", codigo],
        capture_output=True,
        text=True,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": src},
    )
    assert r.returncode == 0, r.stderr  # 134/SIGABRT = widget construído antes do QApplication
    assert "TelaInicial" in r.stdout


def test_sem_config_monta_a_tela_inicial(app):
    # sem --config o programa não morre: abre a tela inicial para o tio escolher o arquivo
    assert isinstance(_widget_de(_parse_args([])), TelaInicial)


def test_com_config_valido_monta_o_dashboard(app, tmp_path):
    widget = _widget_de(_parse_args(["--config", str(_config(tmp_path))]))
    assert isinstance(widget, JanelaMonitor)


def test_defaults_de_taxa_bloco_saida_e_janela():
    args = _parse_args(["--config", "canais.toml"])
    assert args.taxa == 1024.0
    assert args.bloco == 256
    assert args.saida == Path("ensaio.csv")
    assert args.capacidade_janela == 2000
