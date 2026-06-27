from pathlib import Path

from ensaios_ni.dominio.canais import carregar_canais

EXEMPLO = Path(__file__).resolve().parents[2] / "config" / "canais.exemplo.toml"


def test_config_exemplo_carrega_e_e_valido():
    canais = carregar_canais(EXEMPLO)
    assert len(canais) >= 1
    for nome in canais:
        canal = canais[nome]
        assert canal.unidade
        # cada canal é por regressão (reta) OU por segmento (pontos) OU linear (ganho/offset)
        assert canal.reta is not None or canal.pontos is not None or isinstance(canal.ganho, float)


def test_config_exemplo_tem_canal_por_regressao():
    canais = carregar_canais(EXEMPLO)
    assert any(canais[nome].reta is not None for nome in canais)


def test_config_exemplo_tem_canal_por_segmento():
    canais = carregar_canais(EXEMPLO)
    assert any(canais[nome].pontos is not None for nome in canais)


def test_config_exemplo_demonstra_nome_do_sinal():
    # o exemplo deve mostrar o rótulo humano (Nome do Sinal do AqDados), com fallback pro endereço
    canais = carregar_canais(EXEMPLO)
    assert any(canais[nome].rotulo is not None for nome in canais)
