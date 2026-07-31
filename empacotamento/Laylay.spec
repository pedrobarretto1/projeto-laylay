# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

RAIZ = Path(SPECPATH).parent

datas = []
binaries = []
hiddenimports = collect_submodules("mente_laylay")

for pacote in (
    "AppOpener",
    "comtypes",
    "ctranslate2",
    "edge_tts",
    "faster_whisper",
    "PIL",
    "pycaw",
    "pyttsx3",
    "sounddevice",
    "tinytuya",
    "websockets",
    "WMI",
):
    try:
        dados_pkg, binarios_pkg, imports_pkg = collect_all(pacote)
        datas += dados_pkg
        binaries += binarios_pkg
        hiddenimports += imports_pkg
    except Exception:
        pass

a = Analysis(
    [str(RAIZ / "laylay.py")],
    pathex=[str(RAIZ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "matplotlib", "IPython", "jupyter"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Laylay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Laylay",
)
