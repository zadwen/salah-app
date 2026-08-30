"""Entry point for the Windows build of Salah.

Run with: python main.py
Build a standalone .exe with: pyinstaller build/salah-win.spec
"""
import os
import sys

# The pure-logic modules (api/config/constants/i18n/qibla/scheduler)
# live in the shared salah_app/ package at the repo root, one level up
# from this windows/ folder. Add it to sys.path so `import salah_app`
# resolves both when run from source and when frozen by PyInstaller.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)


def main():
    if sys.platform != "win32":
        print("This build targets Windows. On Linux/Mac, run the original "
              "`python3 main.py` from the repo root instead (GTK tray version).")
    from salah_win.app import SalahWinApp
    app = SalahWinApp()
    app.mainloop()


if __name__ == "__main__":
    main()
