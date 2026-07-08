import pytest

from ensaios_ni.dominio.canais import carregar_canais
from ensaios_ni.persistencia.config_canais import (
    ler_pontos,
    remover_canal,
    salvar_afericao,
    salvar_canal,
    salvar_rotulo,
)


def _escrever(tmp_path, conteudo):
    arq = tmp_path / "canais.toml"
    arq.write_text(conteudo, encoding="utf-8")
    return arq


def test_salvar_canal_cria_um_canal_novo(tmp_path):
    # o editor monta a tabela de canais pela tela: adicionar um canal a um perfil ainda sem [canais]
    arq = tmp_path / "novo.toml"
    arq.write_text("", encoding="utf-8")
    salvar_canal(arq, "Mod1/ai0", {"tipo": "tensao", "unidade": "kgf", "ganho": 100.0, "offset": 0.0})

    canal = carregar_canais(arq)["Mod1/ai0"]
    assert canal.tipo == "tensao"
    assert canal.unidade == "kgf"
    assert canal.ganho == 100.0


def test_salvar_canal_edita_preservando_os_outros_canais_e_comentarios(tmp_path):
    arq = _escrever(
        tmp_path,
        '# canais do ensaio\n'
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
    )
    salvar_canal(arq, "Mod1/ai0", {"tipo": "tensao", "unidade": "mm", "ganho": 5.0, "offset": 1.0})

    assert "# canais do ensaio" in arq.read_text(encoding="utf-8")
    canais = carregar_canais(arq)
    assert canais["Mod1/ai0"].unidade == "mm"  # editado
    assert canais["Mod1/ai1"].ganho == 25.0  # preservado


def test_remover_canal_apaga_so_aquele_canal(tmp_path):
    arq = _escrever(
        tmp_path,
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
    )
    remover_canal(arq, "Mod1/ai0")

    canais = carregar_canais(arq)
    assert "Mod1/ai0" not in canais
    assert "Mod1/ai1" in canais


def test_salvar_canal_grava_strain_com_gage_factor(tmp_path):
    # canal de strain: o editor grava o gage_factor por canal (ADR-020); carregar_canais lê os params
    arq = tmp_path / "strain.toml"
    arq.write_text("", encoding="utf-8")
    salvar_canal(
        arq,
        "cDAQ9184-1820306Mod3/ai0",
        {"tipo": "strain", "unidade": "µε", "gage_factor": 2.14, "ganho": 1000000.0, "offset": 0.0},
    )

    canal = carregar_canais(arq)["cDAQ9184-1820306Mod3/ai0"]
    assert canal.tipo == "strain"
    assert canal.strain.gage_factor == 2.14


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
