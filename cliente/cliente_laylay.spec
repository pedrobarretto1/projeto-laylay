# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

raiz = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(raiz / 'cliente' / 'cliente_laylay.py')],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL.ImageGrab'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='cliente_laylay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
