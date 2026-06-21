import ast
from pathlib import Path

RAIZ_SRC = Path(__file__).resolve().parents[2] / "src" / "ensaios_ni"
PERMITIDO = {"daqmx.py"}


def _importa_nidaqmx(arquivo: Path) -> bool:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            if any(alias.name.split(".")[0] == "nidaqmx" for alias in no.names):
                return True
        elif isinstance(no, ast.ImportFrom):
            if (no.module or "").split(".")[0] == "nidaqmx":
                return True
    return False


def arquivos_violando(raiz: Path, permitido: set[str]) -> list[Path]:
    return [arq for arq in raiz.rglob("*.py") if arq.name not in permitido and _importa_nidaqmx(arq)]


def test_nenhum_arquivo_de_producao_importa_nidaqmx_fora_do_daqmx():
    violacoes = arquivos_violando(RAIZ_SRC, PERMITIDO)
    assert violacoes == [], f"import proibido de nidaqmx em: {[str(v) for v in violacoes]}"


def test_detector_pega_import_direto(tmp_path):
    (tmp_path / "ruim.py").write_text("import nidaqmx\n", encoding="utf-8")
    assert [a.name for a in arquivos_violando(tmp_path, PERMITIDO)] == ["ruim.py"]


def test_detector_pega_import_from(tmp_path):
    (tmp_path / "ruim.py").write_text("from nidaqmx.constants import StrainUnits\n", encoding="utf-8")
    assert [a.name for a in arquivos_violando(tmp_path, PERMITIDO)] == ["ruim.py"]


def test_detector_ignora_daqmx_e_mencao_em_docstring(tmp_path):
    (tmp_path / "daqmx.py").write_text("import nidaqmx\n", encoding="utf-8")
    (tmp_path / "porta.py").write_text('"""só menciona nidaqmx no texto, não importa."""\n', encoding="utf-8")
    assert arquivos_violando(tmp_path, PERMITIDO) == []
