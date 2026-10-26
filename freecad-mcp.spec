# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

mcp_datas, mcp_bins, mcp_imports = collect_all("mcp")
validators_datas, validators_bins, validators_imports = collect_all("validators")
a = Analysis(
    ["launcher.py"],
    pathex=["src"],
    binaries=mcp_bins + validators_bins,
    datas=mcp_datas + validators_datas + [
        ("resources/SKILL.md", "resources"),
        ("addon/FreeCADMCP", "addon/FreeCADMCP"),
    ],
    hiddenimports=mcp_imports + validators_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="freecad-mcp", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=True,
)
