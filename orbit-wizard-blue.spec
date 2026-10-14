# -*- mode: python ; coding: utf-8 -*-
"""Portable one-directory Windows build."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

datas = (collect_data_files("astropy") + collect_data_files("astropy_iers_data")
         + collect_data_files("pyqtgraph"))
for distribution in ("orbit-wizard-blue", "sgp4", "numpy", "astropy", "pyerfa"):
    datas += copy_metadata(distribution)
hiddenimports = collect_submodules("pyqtgraph.opengl") + collect_submodules("OpenGL")

a = Analysis(
    ["src/orbit_wizard_blue/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["packaging/hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="orbit-wizard-blue",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="orbit-wizard-blue",
)
