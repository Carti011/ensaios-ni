import ast
from pathlib import Path

RAIZ_SRC = Path(__file__).resolve().parents[2] / "src" / "ensaios_ni"
CAMADA_WIDGET = RAIZ_SRC / "apresentacao" / "qt"


def _importa_pyside(arquivo: Path) -> bool:
    """PySide6 é o framework de UI: só pode ser importado na camada de widget
    (apresentacao/qt/). Em qualquer outro módulo — inclusive o Presenter — é violação,
    para a lógica seguir testável no Mac sem display (à la nidaqmx só no daqmx.py)."""
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    for no in ast.walk(arvore):  # qualquer nível: PySide não pode aparecer nem lazy fora de qt/
        if isinstance(no, ast.Import):
            if any(alias.name.split(".")[0] == "PySide6" for alias in no.names):
                return True
        elif isinstance(no, ast.ImportFrom):
            if (no.module or "").split(".")[0] == "PySide6":
                return True
    return False


def arquivos_violando(raiz: Path, camada_permitida: Path) -> list[Path]:
    return [
        arq
        for arq in raiz.rglob("*.py")
        if _importa_pyside(arq) and camada_permitida not in arq.parents
    ]


def test_pyside_so_na_camada_de_widget():
    violacoes = arquivos_violando(RAIZ_SRC, CAMADA_WIDGET)
    assert violacoes == [], f"PySide6 importado fora de apresentacao/qt/: {[str(v) for v in violacoes]}"


def test_detector_pega_import_de_pyside(tmp_path):
    (tmp_path / "ruim.py").write_text("from PySide6.QtWidgets import QWidget\n", encoding="utf-8")
    assert [a.name for a in arquivos_violando(tmp_path, tmp_path / "qt")] == ["ruim.py"]


def test_detector_ignora_pyside_na_camada_de_widget(tmp_path):
    camada = tmp_path / "qt"
    camada.mkdir()
    (camada / "janela.py").write_text("import PySide6.QtWidgets\n", encoding="utf-8")
    assert arquivos_violando(tmp_path, camada) == []
