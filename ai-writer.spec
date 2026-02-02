# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AI Writer
Run with: pyinstaller ai-writer.spec
"""

import os
import sys

block_cipher = None

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')

a = Analysis(
    [os.path.join(SRC_PATH, 'ai_writer', 'main.py')],
    pathex=[SRC_PATH],
    binaries=[],
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=[
        'ai_writer',
        'ai_writer.agents',
        'ai_writer.models',
        'ai_writer.orchestrators',
        'ai_writer.processors',
        'ai_writer.readers',
        'ai_writer.utils',
        'ai_writer.writers',
        'typer',
        'rich',
        'pydantic',
        'openai',
        'sklearn',
        'sklearn.metrics.pairwise',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-writer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True para aplicación de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Puedes añadir: icon='icon.ico'
)
