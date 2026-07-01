import os

import pytest

# o widget só existe com o extra [gui]; sem PySide/pyqtgraph, pula (domínio não depende disso)
pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # roda headless, sem display

from PySide6.QtCore import Qt  # noqa: E402

from ensaios_ni.apresentacao.afericao import Afericao  # noqa: E402
from ensaios_ni.apresentacao.exportacao import Exportacao  # noqa: E402
from ensaios_ni.apresentacao.monitor import EstadoMonitor, MonitorAoVivo  # noqa: E402
from ensaios_ni.apresentacao.qt.janela import (  # noqa: E402
    JanelaMonitor,
    PainelAfericao,
    PainelExportacao,
)
from ensaios_ni.aquisicao.fake import AquisicaoFake  # noqa: E402
from ensaios_ni.dominio.canais import Canais, Canal, carregar_canais  # noqa: E402
from ensaios_ni.persistencia.csv_ensaio import gravar_ensaio  # noqa: E402
from ensaios_ni.persistencia.metadata_ensaio import ler_metadata  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _monitor(tmp_path) -> MonitorAoVivo:
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0, 3.0, 4.0]})
    canais = Canais(
        {"Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0)}
    )
    return MonitorAoVivo(
        fonte, canais, taxa_hz=4.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )


def _monitor_multiunidade(tmp_path) -> MonitorAoVivo:
    fonte = AquisicaoFake(
        tensoes={"Mod1/ai0": [1.0, 2.0], "Mod1/ai1": [1.0, 2.0]},
        strains={"Mod3/ai0": [0.001, 0.001]},
    )
    canais = Canais(
        {
            "Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0),
            "Mod1/ai1": Canal(nome="Mod1/ai1", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0),
            "Mod3/ai0": Canal(
                nome="Mod3/ai0", tipo="strain", unidade="µε", ganho=1_000_000.0, offset=0.0
            ),
        }
    )
    return MonitorAoVivo(
        fonte, canais, taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv"
    )


def _monitor_rotulado(tmp_path):
    canais = Canais(
        {
            "Mod1/ai0": Canal(
                nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0, rotulo="Carga"
            ),
            "Mod3/ai0": Canal(
                nome="Mod3/ai0", tipo="strain", unidade="µε", ganho=1_000_000.0, offset=0.0,
                rotulo="Sg1 bico",
            ),
        }
    )
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]}, strains={"Mod3/ai0": [0.001, 0.001]})
    monitor = MonitorAoVivo(fonte, canais, taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv")
    return monitor, canais


def test_tabela_e_seletores_exibem_rotulo_com_endereco_interno(app, tmp_path):
    monitor, canais = _monitor_rotulado(tmp_path)
    janela = JanelaMonitor(monitor, canais=canais)
    # a tabela mostra o rótulo humano; o endereço físico fica guardado internamente
    item = janela._tabela.item(0, 0)
    assert item.text() == "Carga"
    assert item.data(Qt.ItemDataRole.UserRole) == "Mod1/ai0"
    # os seletores X/Y também exibem o rótulo, mapeando para o endereço
    assert janela._combo_x.itemText(0) == "Carga"
    assert janela._combo_x.itemData(0) == "Mod1/ai0"


def _config_real(tmp_path):
    arq = tmp_path / "canais.toml"
    arq.write_text(
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'rotulo = "Carga"\n'
        'pontos = [[0.0, 0.0], [10.0, 1000.0]]\n'
        '\n'
        '[canais."Mod3/ai0"]\n'
        'tipo = "strain"\n'
        'unidade = "µε"\n'
        'rotulo = "Sg1 bico"\n'
        'ganho = 1000000.0\n'
        'offset = 0.0\n',
        encoding="utf-8",
    )
    return arq


def _monitor_de(arq, tmp_path):
    canais = carregar_canais(arq)
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]}, strains={"Mod3/ai0": [0.001, 0.001]})
    monitor = MonitorAoVivo(fonte, canais, taxa_hz=2.0, amostras_por_bloco=2, caminho=tmp_path / "e.csv")
    return monitor, canais


def test_painel_afericao_mostra_pontos_e_correlacao(app):
    af = Afericao(pontos=[(0.0, 0.0), (5.0, 500.0), (10.0, 1000.0)])
    painel = PainelAfericao(af, unidade="kgf", titulo_sinal="Carga")
    assert painel._tabela.rowCount() == 3
    assert "100,00 %" in painel._lbl_correlacao.text()


def test_painel_afericao_botoes_em_portugues_e_aplicar_so_com_reta(app):
    # português total: nada de "Apply"/"Cancel"; e Aplicar só habilita com ao menos 2 pontos
    af = Afericao(pontos=[(0.0, 0.0)])
    painel = PainelAfericao(af, unidade="kgf", titulo_sinal="Carga")
    textos = {painel._botoes.buttons()[i].text() for i in range(len(painel._botoes.buttons()))}
    assert textos == {"Aplicar", "Cancelar"}
    assert painel._btn_aplicar.isEnabled() is False  # 1 ponto: sem reta
    painel._anexar_linha(5.0, 500.0)  # 2 pontos na tabela -> reta válida
    assert painel._btn_aplicar.isEnabled() is True


def test_painel_afericao_mostra_ganho_k_e_inverso(app):
    # espelha o AqDados: Ganho K (V/un) e Ganho 1/K (un/V), com a unidade do canal
    af = Afericao(pontos=[(0.0, 0.0), (5.0, 500.0), (10.0, 1000.0)])  # a = 100 un/V
    painel = PainelAfericao(af, unidade="kgf", titulo_sinal="Carga")
    assert "100,0000 kgf/V" in painel._lbl_ganho_1k.text()
    assert "0,0100 V/kgf" in painel._lbl_ganho_k.text()


def test_painel_afericao_capturar_adiciona_linha_com_a_tensao_lida(app):
    # clicar "Capturar tensão" põe a tensão lida ao vivo numa nova linha, valor em branco (o tio digita)
    painel = PainelAfericao(Afericao(capturar=lambda: 2.5), unidade="kgf", titulo_sinal="Carga")
    antes = painel._tabela.rowCount()
    painel._capturar_tensao()
    assert painel._tabela.rowCount() == antes + 1
    linha = painel._tabela.rowCount() - 1
    assert painel._tabela.item(linha, 0).text() == "2,5000"  # tensão capturada (BR)
    assert painel._tabela.item(linha, 1).text() == ""  # valor de engenharia em branco


def test_painel_afericao_sem_captura_desabilita_o_botao(app):
    # canal sem captura (ex.: strain, ou janela sem fonte): o botão fica desabilitado
    painel = PainelAfericao(Afericao(), unidade="µε", titulo_sinal="Sg1 bico")
    assert painel._btn_capturar.isEnabled() is False


def test_painel_afericao_aplicar_persiste_no_toml(app, tmp_path):
    arq = _config_real(tmp_path)
    af = Afericao(caminho=arq, canal="Mod1/ai0", pontos=[(0.0, 0.0), (5.0, 500.0), (10.0, 1000.0)])
    painel = PainelAfericao(af, unidade="kgf", titulo_sinal="Carga")
    painel._aplicar()

    canal = carregar_canais(arq)["Mod1/ai0"]
    assert canal.reta is not None
    assert canal.reta.a == pytest.approx(100.0)


def test_janela_abre_afericao_pre_preenchida_do_toml(app, tmp_path):
    arq = _config_real(tmp_path)
    monitor, canais = _monitor_de(arq, tmp_path)
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    painel = janela._abrir_afericao("Mod1/ai0")
    assert isinstance(painel, PainelAfericao)
    assert painel._tabela.rowCount() == 2  # pré-preenchido com os pontos do TOML


def test_afericao_captura_a_tensao_ao_vivo_de_canal_de_tensao(app, tmp_path):
    arq = _config_real(tmp_path)
    canais = carregar_canais(arq)
    # fake com amostras suficientes para a média de uma leitura de aferição (o "Leitura do A/D")
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.5] * 100}, strains={"Mod3/ai0": [0.001] * 100})
    monitor = MonitorAoVivo(fonte, canais, taxa_hz=100.0, amostras_por_bloco=10, caminho=tmp_path / "e.csv")
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    painel = janela._abrir_afericao("Mod1/ai0")
    assert painel._afericao.capturar_tensao() == pytest.approx(1.5)  # lê da fonte, sem digitar


def test_afericao_de_strain_nao_captura_tensao(app, tmp_path):
    # strain (9235) não se afere por pontos de tensão: sem captura ao vivo
    arq = _config_real(tmp_path)
    monitor, canais = _monitor_de(arq, tmp_path)
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    painel = janela._abrir_afericao("Mod3/ai0")
    assert painel._afericao.capturar_tensao() is None


def test_editar_rotulo_na_tabela_persiste_no_toml(app, tmp_path):
    arq = _config_real(tmp_path)
    monitor, canais = _monitor_de(arq, tmp_path)
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    # editar o texto do sinal (coluna 0) renomeia o canal e salva no TOML
    janela._tabela.item(0, 0).setText("Carga principal")

    canal = carregar_canais(arq)["Mod1/ai0"]
    assert canal.rotulo == "Carga principal"


def test_alternar_checkbox_nao_apaga_o_rotulo(app, tmp_path):
    arq = _config_real(tmp_path)
    monitor, canais = _monitor_de(arq, tmp_path)
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    # ocultar/mostrar pelo checkbox não pode disparar renomeação
    janela._definir_visivel("Mod1/ai0", False)
    assert carregar_canais(arq)["Mod1/ai0"].rotulo == "Carga"


def test_aplicar_afericao_na_janela_recarrega_calibracao_no_monitor(app, tmp_path):
    arq = _config_real(tmp_path)
    monitor, canais = _monitor_de(arq, tmp_path)
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    # Mod1/ai0 vinha com reta a=100; reafere para a=50 e aplica
    painel = janela._abrir_afericao("Mod1/ai0")
    painel._afericao.definir_pontos([(0.0, 0.0), (5.0, 250.0), (10.0, 500.0)])
    painel._aplicar()
    # a nova calibração vale do próximo Iniciar: fonte [1.0, 2.0] * 50 -> 50, 100 (não 100, 200)
    janela.iniciar()
    janela._ao_passo()
    assert janela._monitor.valor_atual("Mod1/ai0") == 100.0
    janela.parar()


def test_aferir_desabilitado_durante_a_aquisicao(app, tmp_path):
    arq = _config_real(tmp_path)
    monitor, canais = _monitor_de(arq, tmp_path)
    janela = JanelaMonitor(monitor, canais=canais, caminho_config=arq)
    assert janela._btn_aferir.isEnabled() is True  # parado, com config: pode aferir
    janela.iniciar()
    assert janela._btn_aferir.isEnabled() is False  # adquirindo: calibração fica fixa
    janela.parar()
    assert janela._btn_aferir.isEnabled() is True


def test_botao_zerar_habilita_so_adquirindo_e_tara_os_canais(app, tmp_path):
    janela = JanelaMonitor(_monitor(tmp_path))
    assert janela._btn_zerar.isEnabled() is False  # parado: não há repouso a capturar
    janela.iniciar()
    assert janela._btn_zerar.isEnabled() is True
    janela._btn_zerar.click()  # zera: o próximo bloco de repouso vira o zero
    janela._ao_passo()  # [1.0, 2.0] -> 10, 20 (ganho 10); tara 15 -> -5, 5
    assert janela._monitor.valor_atual("Mod1/ai0") == 5.0
    janela.parar()
    assert janela._btn_zerar.isEnabled() is False


def _csv_gravado(tmp_path):
    origem = tmp_path / "ensaio.csv"
    gravar_ensaio(
        origem,
        {"Mod1/ai0": [1.0, 2.0], "Mod3/ai0": [10.0, 20.0]},
        taxa_hz=2.0,
        unidades={"Mod1/ai0": "kgf", "Mod3/ai0": "µε"},
    )
    return origem


def test_painel_exportacao_lista_formatos_e_sinais(app, tmp_path):
    painel = PainelExportacao(Exportacao(_csv_gravado(tmp_path)))
    assert painel._combo_formato.count() == 3  # csv-excel-br, txt-aqanalysis, xlsx
    assert painel._lista_sinais.count() == 2  # Mod1/ai0 e Mod3/ai0, marcados por padrão


def test_painel_exportacao_exporta_no_formato_escolhido(app, tmp_path):
    painel = PainelExportacao(Exportacao(_csv_gravado(tmp_path)))
    painel._combo_formato.setCurrentText("csv-excel-br")
    destino = tmp_path / "saida.csv"
    painel.exportar_para(destino)
    assert destino.exists()
    assert ";" in destino.read_text(encoding="utf-8-sig")


def test_botao_exportar_habilita_apos_ensaio_e_abre_painel(app, tmp_path):
    janela = JanelaMonitor(_monitor(tmp_path))
    assert janela._btn_exportar.isEnabled() is False  # nenhum ensaio gravado ainda
    janela.iniciar()
    janela._ao_passo()
    janela.parar()  # CSV gravado: pode exportar
    assert janela._btn_exportar.isEnabled() is True
    painel = janela._abrir_exportacao()
    assert isinstance(painel, PainelExportacao)


def test_botao_exportar_ignora_csv_residual_de_sessao_anterior(app, tmp_path):
    residual = tmp_path / "e.csv"  # arquivo de uma sessão anterior já em disco
    residual.write_text("tempo_s,Mod1/ai0 (kgf)\n0.0,1.0\n0.01,2.0\n", encoding="utf-8")
    fonte = AquisicaoFake(tensoes={"Mod1/ai0": [1.0, 2.0]})
    canais = Canais(
        {"Mod1/ai0": Canal(nome="Mod1/ai0", tipo="tensao", unidade="kgf", ganho=10.0, offset=0.0)}
    )
    monitor = MonitorAoVivo(fonte, canais, taxa_hz=2.0, amostras_por_bloco=2, caminho=residual)
    janela = JanelaMonitor(monitor)
    assert janela._btn_exportar.isEnabled() is False  # nada gravado nesta sessão: não exporta


def test_parar_salva_a_metadata_ao_lado_do_csv(app, tmp_path):
    janela = JanelaMonitor(_monitor(tmp_path))
    janela._campo_obra.setText("Ponte X")
    janela._campo_operador.setText("Weslley")
    janela.iniciar()
    janela._ao_passo()  # grava um bloco
    janela.parar()
    meta = ler_metadata(janela._monitor.caminho)
    assert meta.obra == "Ponte X" and meta.operador == "Weslley"


def test_janela_monta_inicia_e_processa_um_passo(app, tmp_path):
    janela = JanelaMonitor(_monitor(tmp_path))
    janela.iniciar()
    assert janela._monitor.estado is EstadoMonitor.ADQUIRINDO
    janela._ao_passo()
    assert janela._monitor.valor_atual("Mod1/ai0") == 20.0
    janela.parar()
    assert janela._monitor.estado is EstadoMonitor.PARADO


def test_janela_empilha_um_subplot_por_unidade(app, tmp_path):
    janela = JanelaMonitor(_monitor_multiunidade(tmp_path))
    # dois canais kgf dividem um sub-plot; µε no seu próprio → 2 sub-plots, não 3
    assert list(janela._graficos.keys()) == ["kgf", "µε"]
    janela.iniciar()
    janela._ao_passo()
    assert janela._monitor.valor_atual("Mod3/ai0") == 1000.0
    janela.parar()


def test_janela_plota_xy_carga_deformacao(app, tmp_path):
    janela = JanelaMonitor(_monitor_multiunidade(tmp_path))
    # default: carga (primeiro canal) no X, deformação (último) no Y
    assert janela._canal_x == "Mod1/ai0"
    assert janela._canal_y == "Mod3/ai0"
    janela.iniciar()
    janela._ao_passo()
    par = janela._par_xy_atual()
    assert par is not None
    assert len(par.xs) == len(par.ys) > 0
    janela.parar()


def test_janela_oculta_e_revela_canal_pela_selecao(app, tmp_path):
    janela = JanelaMonitor(_monitor_multiunidade(tmp_path))
    janela.iniciar()
    janela._ao_passo()
    # todos visíveis por padrão: a curva tem dados
    assert janela._esta_visivel("Mod1/ai1") is True
    xs, _ = janela._curvas["Mod1/ai1"].getData()
    assert xs is not None and len(xs) > 0

    # desmarcar esconde a curva (mas não para a gravação nem mexe no XY)
    janela._definir_visivel("Mod1/ai1", False)
    assert janela._esta_visivel("Mod1/ai1") is False
    xs, _ = janela._curvas["Mod1/ai1"].getData()
    assert xs is None or len(xs) == 0

    # remarcar volta a desenhar no próximo passo
    janela._definir_visivel("Mod1/ai1", True)
    janela._ao_passo()
    xs, _ = janela._curvas["Mod1/ai1"].getData()
    assert xs is not None and len(xs) > 0
    janela.parar()


def test_janela_recolhe_subplot_quando_unidade_fica_sem_canais(app, tmp_path):
    janela = JanelaMonitor(_monitor_multiunidade(tmp_path))
    # multiunidade: Mod1/ai0 e Mod1/ai1 em kgf, Mod3/ai0 em µε
    assert janela._subplots_visiveis() == ["kgf", "µε"]

    janela._definir_visivel("Mod1/ai0", False)
    assert janela._subplots_visiveis() == ["kgf", "µε"]  # ainda há Mod1/ai1 em kgf

    janela._definir_visivel("Mod1/ai1", False)
    assert janela._subplots_visiveis() == ["µε"]  # unidade kgf sem canais: recolhe

    janela._definir_visivel("Mod1/ai0", True)
    assert janela._subplots_visiveis() == ["kgf", "µε"]  # volta ao reaparecer um canal
