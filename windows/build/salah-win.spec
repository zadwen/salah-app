# PyInstaller spec for Salah (Windows).
# Build from the windows/ folder with:
#   pyinstaller build/salah-win.spec --distpath dist --workpath build/_work
#
# Produces a single-file, windowed (no console) salah.exe.

import os

block_cipher = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))
SALAH_APP_DIR = os.path.join(REPO_ROOT, "salah_app")

a = Analysis(
    [os.path.join(os.path.dirname(SPEC), "..", "main.py")],
    pathex=[REPO_ROOT, os.path.dirname(SPEC) and os.path.join(os.path.dirname(SPEC), "..")],
    binaries=[],
    datas=[
        (os.path.join(SALAH_APP_DIR, "resources"), "salah_app/resources"),
        (os.path.join(os.path.dirname(SPEC), "..", "salah_win", "resources"), "salah_win/resources"),
    ],
    hiddenimports=["PIL._tkinter_finder"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["gi"],  # never pull in the GTK bindings on the Windows build
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
    name="salah",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # windowed app, no terminal flash
    icon=None,           # icon is generated at runtime via Pillow
)
