# -*- mode: python ; coding: utf-8 -*-
# =====================================================================
# SIGBEF — PyInstaller spec
#
# Para gerar o executável:
#     pyinstaller sigbef.spec
#
# O resultado fica em dist/SIGBEF/  (modo onedir, recomendado)
# =====================================================================

from pathlib import Path

block_cipher = None
PROJECT = Path.cwd()

# Detecta o ícone se existir
_icon_path = PROJECT / "assets" / "sigbef.ico"
APP_ICON = str(_icon_path) if _icon_path.exists() else None


a = Analysis(
    ['sigbef.py'],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=[
        # Inclui o pacote sigbef inteiro
        ('sigbef', 'sigbef'),
        # Inclui assets estáticos (se existirem)
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'sigbef',
        'sigbef.app',
        'sigbef.auth',
        'sigbef.barcode_util',
        'sigbef.database',
        'sigbef.formato',
        'sigbef.isbn_lookup',
        'sigbef.seed',
        'sigbef.servicos',
        'sigbef.ui_dialogos',
        'sigbef.ui_login',
        'sigbef.ui_painel',
        'sigbef.ui_selfservice',
        'sigbef.ui_tema',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas', 'PyQt5', 'PyQt6',
        'PySide2', 'PySide6', 'IPython', 'jupyter', 'notebook',
        'pytest', 'sphinx',
    ],
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
    name='SIGBEF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,            # Aplicação GUI (sem janela de console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,  # Ícone da aplicação (None se não existir)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SIGBEF',
)

# No macOS, embrulha o resultado num bundle .app clicável no Finder
import sys
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='SIGBEF.app',
        icon=None,
        bundle_identifier='br.gov.rn.cefe.sigbef',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleDisplayName': 'SIGBEF',
            'CFBundleShortVersionString': '1.6.2',
        },
    )
