# -*- mode: python ; coding: utf-8 -*-

import os
from glob import glob

# Импортируем классы PyInstaller для работы с версией Windows
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct,
)

# ==============================================================================
# УКАЖИТЕ ВЕРСИЮ ЗДЕСЬ
# ==============================================================================
APP_VERSION = '0.2.0'
COPYRIGHT = '© 2026 Dmitry Maksimov'
# ==============================================================================

# Преобразуем '0.2.0' в кортеж чисел (0, 2, 0, 0) для структуры Windows
version_tuple = tuple(map(int, APP_VERSION.split('.')))
if len(version_tuple) == 3:
    version_tuple += (0,)

# Формируем объект метаданных версии для Windows
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=version_tuple,
        prodvers=version_tuple,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904B0',
                [
                    StringStruct('FileVersion', APP_VERSION),
                    StringStruct('ProductVersion', APP_VERSION),
                    StringStruct('FileDescription', 'LLM Server Controller'),
                    StringStruct('InternalName', 'LLMServerController'),
                    StringStruct('OriginalFilename', 'LLMServerController.exe'),
                    StringStruct('ProductName', 'LLM Server Controller'),
					StringStruct('LegalCopyright', COPYRIGHT),
                ],
            )
        ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])]),
    ],
)

project_dir = os.path.abspath(os.getcwd())
icon_dir = os.path.join(project_dir, 'icon')
icon_png_candidates = [
    os.path.join(icon_dir, '256x256.png'),
    os.path.join(icon_dir, '64x64.png'),
    os.path.join(icon_dir, '32x32.png'),
    os.path.join(icon_dir, '24x24.png'),
    os.path.join(icon_dir, '16x16.png'),
    os.path.join(icon_dir, 'icon48x48.png'),
]
icon_png = next((path for path in icon_png_candidates if os.path.exists(path)), None)
icon_ico_candidates = [
    os.path.join(icon_dir, '256x256.ico'),
    os.path.join(icon_dir, '64x64.ico'),
    os.path.join(icon_dir, '48x48.ico'),
    os.path.join(icon_dir, '32x32.ico'),
    os.path.join(icon_dir, '24x24.ico'),
    os.path.join(icon_dir, '16x16.ico'),
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
    version=version_info,  # <-- Передаем сгенерированный объект версии
)