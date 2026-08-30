"""Run-at-startup toggle for Windows.

Uses the per-user registry Run key (HKCU) rather than a shortcut in
the Startup folder -- no admin rights needed, and it's the standard
mechanism most Windows tray utilities use. Registers whatever is
currently running: the frozen .exe if this is a PyInstaller build, or
`pythonw.exe main.py` if running from source (pythonw avoids a console
window flashing on login).
"""
import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SalahApp"


def _winreg():
    import winreg
    return winreg


def _startup_command():
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-built salah.exe
        return f'"{sys.executable}" --minimized'
    # Running from source: prefer pythonw.exe (no console window) if present
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    interpreter = pythonw if os.path.exists(pythonw) else sys.executable
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{interpreter}" "{main_py}" --minimized'


def is_enabled():
    if sys.platform != "win32":
        return False
    try:
        winreg = _winreg()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except Exception:
        return False


def set_enabled(enabled):
    """Returns True on success, False if it couldn't be set (e.g. not
    on Windows, or registry access denied) -- callers should treat a
    False return as "toggle didn't take" and let the user know."""
    if sys.platform != "win32":
        return False
    try:
        winreg = _winreg()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _startup_command())
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False
