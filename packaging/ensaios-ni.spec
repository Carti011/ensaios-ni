# -*- mode: python ; coding: utf-8 -*-
# Build do executável do dashboard de hardware (Fase 6 — ADR-022).
#
# Rodar NO WINDOWS, a partir da raiz do projeto:
#     pip install -e .[hardware,gui,excel,build]
#     pyinstaller packaging/ensaios-ni.spec
# Saída: dist/ensaios-ni.exe (um único arquivo, sem console).
#
# O driver NI-DAQmx nativo NÃO vai no bundle — é gratuito da NI e instalado à parte na máquina;
# aqui embutimos só o wrapper Python `nidaqmx`.

from PyInstaller.utils.hooks import collect_submodules, copy_metadata


def _submodulos(pacote):
    # pyqtgraph/nidaqmx/openpyxl carregam módulos dinamicamente que a análise estática não vê.
    # Defensivo: se um pacote não estiver instalado (ex.: build sem um extra), não quebra o build.
    try:
        return collect_submodules(pacote)
    except Exception:
        return []


def _metadados(pacote):
    # nidaqmx e nitypes leem a própria versão via importlib.metadata em tempo de execução
    # (`version(__name__)`); sem o .dist-info empacotado, isso vira "No package metadata was
    # found for ..." só quando o Iniciar dispara o import lazy do nidaqmx.
    try:
        return copy_metadata(pacote)
    except Exception:
        return []


ocultos = _submodulos("pyqtgraph") + _submodulos("nidaqmx") + _submodulos("openpyxl")
metadados = _metadados("nidaqmx") + _metadados("nitypes")

analise = Analysis(
    ["../src/ensaios_ni/apresentacao/qt/hardware.py"],  # entrypoint: tela inicial sem CLI
    pathex=["../src"],
    binaries=[],
    datas=metadados,
    hiddenimports=ocultos,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "matplotlib"],  # não usados em runtime; enxugam o binário
    noarchive=False,
)

pyz = PYZ(analise.pure)

exe = EXE(
    pyz,
    analise.scripts,
    analise.binaries,
    analise.datas,
    [],
    name="ensaios-ni",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,  # app gráfico: sem janela de terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
)
