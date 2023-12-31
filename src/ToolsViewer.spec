# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main_tools_viewer.py'],
    pathex=['./'],
    binaries=[],
    datas=[('Config/*.cfg', 'Config'), ('font/*.ttf', 'font'), ('icons/*.ico', 'icons'), ('icons/*.png', 'icons')],
    hiddenimports=['core.classes.node', 'misc.color', 'libs.p4util', 'libs.constants', 'wx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ToolsViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/ToolsViewer.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ToolsViewer',
)
