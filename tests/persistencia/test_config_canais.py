import pytest

from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.persistencia.config_canais import ler_pontos, salvar_afericao, salvar_rotulo


def _escrever(tmp_path, conteudo):
    arq = tmp_path / "canais.toml"
    arq.write_text(conteudo, encoding="utf-8")
    return arq


def test_salvar_afericao_grava_pontos_que_viram_reta(tmp_path):
    # aferir um canal linear: grava os pontos; ao reler, o canal passa a ser por regressão
    arq = _escrever(
        tmp_path,
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
    )
    salvar_afericao(arq, "Mod1/ai0", pontos=[(0.0, 0.0), (5.0, 500.0), (10.0, 1000.0)])

    canal = carregar_canais(arq)["Mod1/ai0"]
    assert canal.reta is not None
    assert canal.reta.a == pytest.approx(100.0)
    assert canal.reta.b == pytest.approx(0.0)
    assert canal.reta.correlacao == pytest.approx(1.0)


def test_salvar_afericao_preserva_comentarios_e_outros_canais(tmp_path):
    # o arquivo é editado por humano: aferir um canal não pode apagar comentários nem mexer no resto
    arq = _escrever(
        tmp_path,
        '# calibração dos canais do ensaio\n'
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n'
        '\n'
        '# transdutor de pressão\n'
        '[canais."Mod1/ai1"]\n'
        'tipo = "tensao"\n'
        'unidade = "bar"\n'
        'ganho = 25.0\n'
        'offset = 0.0\n',
    )
    salvar_afericao(arq, "Mod1/ai0", pontos=[(0.0, 0.0), (10.0, 1000.0)])

    texto = arq.read_text(encoding="utf-8")
    assert "# calibração dos canais do ensaio" in texto
    assert "# transdutor de pressão" in texto
    canais = carregar_canais(arq)
    assert canais["Mod1/ai1"].ganho == pytest.approx(25.0)


def test_salvar_afericao_remove_ganho_offset_linear_orfaos(tmp_path):
    # a calibração por pontos substitui a conversão linear; ganho/offset não podem ficar órfãos
    arq = _escrever(
        tmp_path,
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
    )
    salvar_afericao(arq, "Mod1/ai0", pontos=[(0.0, 0.0), (10.0, 1000.0)])

    texto = arq.read_text(encoding="utf-8")
    assert "ganho" not in texto
    assert "offset" not in texto


def test_ler_pontos_devolve_a_tabela_de_calibracao_do_canal(tmp_path):
    # ao reabrir a aferição, o painel recupera os pontos do TOML (o Canal só guarda a reta)
    arq = _escrever(
        tmp_path,
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'pontos = [[0.0, 0.0], [5.0, 500.0]]\n',
    )
    assert ler_pontos(arq, "Mod1/ai0") == [(0.0, 0.0), (5.0, 500.0)]


def test_ler_pontos_vazio_quando_canal_e_linear(tmp_path):
    arq = _escrever(
        tmp_path,
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
    )
    assert ler_pontos(arq, "Mod1/ai0") == []


def test_salvar_rotulo_grava_nome_do_sinal(tmp_path):
    arq = _escrever(
        tmp_path,
        '[canais."Mod1/ai0"]\n'
        'tipo = "tensao"\n'
        'unidade = "kgf"\n'
        'ganho = 100.0\n'
        'offset = 0.0\n',
    )
    salvar_rotulo(arq, "Mod1/ai0", "Carga")

    canal = carregar_canais(arq)["Mod1/ai0"]
    assert canal.rotulo == "Carga"
    assert canal.etiqueta == "Carga"
