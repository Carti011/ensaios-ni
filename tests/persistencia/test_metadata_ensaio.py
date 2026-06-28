from ensaios_ni.dominio.metadata import Metadata
from ensaios_ni.persistencia.metadata_ensaio import gravar_metadata, ler_metadata


def test_grava_e_le_metadata_ao_lado_do_csv(tmp_path):
    csv = tmp_path / "ensaio.csv"
    meta = Metadata(
        obra="Ponte Rio-Niterói", operador="Weslley", data="2026-06-27", observacao="prova de carga"
    )
    gravar_metadata(csv, meta)
    assert (tmp_path / "ensaio.meta.toml").exists()  # par ao lado do CSV
    assert ler_metadata(csv) == meta


def test_ler_metadata_inexistente_devolve_vazia(tmp_path):
    assert ler_metadata(tmp_path / "ensaio.csv") == Metadata()
