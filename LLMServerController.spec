# -*- mode: python ; coding: utf-8 -*-

import os
from glob import glob

project_dir = os.path.abspath(os.getcwd())
icon_dir = os.path.join(project_dir, 'icon')
icon_png_candidates = [
    os.path.join(icon_dir, '256х256.png'),
    os.path.join(icon_dir, '64х64.png'),
    os.path.join(icon_dir, '32х32.png'),
    os.path.join(icon_dir, '24х24.png'),
    os.path.join(icon_dir, '16х16.png'),
    os.path.join(icon_dir, 'icon48х48.png'),
]
icon_png = next((path for path in icon_png_candidates if os.path.exists(path)), None)
icon_ico_candidates = [
    os.path.join(icon_dir, '256х256.ico'),
    os.path.join(icon_dir, '64х64.ico'),
    os.path.join(icon_dir, '48х48.ico'),
    os.path.join(icon_dir, '32х32.ico'),
    os.path.join(icon_dir, '24х24.ico'),
    os.path.join(icon_dir, '16х16.ico'),
]
icon_ico = next((path for path in icon_ico_candidates if os.path.exists(path)), None)
if icon_ico is None:
    fallback_ico_files = sorted(glob(os.path.join(icon_dir, '*.ico')))
    icon_ico = fallback_ico_files[0] if fallback_ico_files else None

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('icon', 'icons'),
    ],
    hiddenimports=[],
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
    name='LLMServerController',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_ico,
)