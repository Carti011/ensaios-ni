import ast
from pathlib import Path

RAIZ_SRC = Path(__file__).resolve().parents[2] / "src" / "ensaios_ni"


def _importa_openpyxl_no_topo(arquivo: Path) -> bool:
    """openpyxl é extra opcional [excel]: só pode ser importado lazy (dentro de função),
    nunca no nível de módulo, senão o pacote quebra ao importar sem openpyxl instalado."""
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    for no in arvore.body:  # só o nível de módulo; imports dentro de funções são lazy (ok)
        if isinstance(no, ast.Import):
            if any(alias.name.split(".")[0] == "openpyxl" for alias in no.names):
                return True
        elif isinstance(no, ast.ImportFrom):
            if (no.module or "").split(".")[0] == "openpyxl":
                return True
    return False


def arquivos_violando(raiz: Path) -> list[Path]:
    return [arq for arq in raiz.rglob("*.py") if _importa_openpyxl_no_topo(arq)]


def test_nenhum_modulo_importa_openpyxl_no_nivel_de_modulo():
    violacoes = arquivos_violando(RAIZ_SRC)
    assert violacoes == [], f"import top-level de openpyxl (deve ser lazy) em: {[str(v) for v in violacoes]}"


def test_detector_pega_import_no_topo(tmp_path):
    (tmp_path / "ruim.py").write_text("from openpyxl import Workbook\n", encoding="utf-8")
    assert [a.name for a in arquivos_violando(tmp_path)] == ["ruim.py"]


def test_detector_ignora_import_lazy_dentro_de_funcao(tmp_path):
    (tmp_path / "ok.py").write_text(
        "def exportar():\n    from openpyxl import Workbook\n    return Workbook()\n",
        encoding="utf-8",
    )
    assert arquivos_violando(tmp_path) == []
