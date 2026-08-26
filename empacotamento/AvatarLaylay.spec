# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

RAIZ = Path(SPECPATH).parent
datas = []
binaries = []
hiddenimports = collect_submodules("mente_laylay.personalidade")
for pacote in ("PIL", "psutil"):
    try:
        dados_pkg, binarios_pkg, imports_pkg = collect_all(pacote)
        datas += dados_pkg
        binaries += binarios_pkg
        hiddenimports += imports_pkg
    except Exception:
        pass

a = Analysis(
    [str(RAIZ / "cliente" / "avatar_laylay.py")],
    pathex=[str(RAIZ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AvatarLaylay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
)
