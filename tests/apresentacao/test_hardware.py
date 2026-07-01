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
