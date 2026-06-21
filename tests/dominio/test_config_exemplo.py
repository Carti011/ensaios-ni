from pathlib import Path

from ensaios_ni.dominio.canais import carregar_canais

EXEMPLO = Path(__file__).resolve().parents[2] / "config" / "canais.exemplo.toml"


def test_config_exemplo_carrega_e_e_valido():
    canais = carregar_canais(EXEMPLO)
    assert len(canais) >= 1
    for nome in canais:
        canal = canais[nome]
        assert canal.unidade
        assert isinstance(canal.ganho, float)
