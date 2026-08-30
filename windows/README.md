# Salah for Windows

A native Windows build of the Salah prayer-times app. The Linux
version is built on GTK3/AppIndicator3, which don't exist on Windows,
so this is a separate UI layer (Tkinter + a system tray icon via
`pystray`) sitting on top of the same prayer-time logic
(`salah_app/api.py`, `config.py`, `scheduler.py`, `qibla.py`, `i18n.py`
— none of those import GTK, so they're shared as-is).

## What's different from the Linux version

- **Manual time adjustment.** Settings now has a per-prayer +/- minute
  offset, so you can nudge Fajr, Dhuhr, etc. to match your local
  mosque's iqama time if the raw Aladhan calculation is a few minutes
  off. This was missing before — there was genuinely no field for it.
- **Mute button.** A speaker icon in the top bar and in the tray menu
  mutes notification sound instantly. Muting never hides the
  notification itself — you still see it, it's just silent — so you
  never miss that a prayer time arrived.
- **Full dashboard window**, not just a tray dropdown: a live
  countdown to the next prayer, a 6-card grid for today's times with
  the upcoming one highlighted, Hijri date, and a Qibla compass.
- **Themed notifications.** Instead of relying on Windows' native
  toast (which behaves inconsistently once an app is packaged with
  PyInstaller), notifications are a small themed banner the app draws
  itself in the bottom-right corner — this is also what makes Mute
  100% reliable, since the app controls the whole notification path.

## Running from source

```powershell
cd windows
python -m pip install -r requirements.txt
python main.py
```

Requires Python 3.10+ from python.org (make sure "tcl/tk and IDLE" is
checked in the installer — that's what provides `tkinter`).

## Building a standalone .exe

```powershell
cd windows
pip install -r requirements.txt
pyinstaller build/salah-win.spec --distpath dist --workpath build/_work
```

This produces `windows/dist/salah.exe` — a single windowed executable,
no console flash, no Python install required on the machine that runs it.

A GitHub Actions workflow (`.github/workflows/build-windows.yml`) also
builds this automatically on every push to `windows/` or `salah_app/`,
and uploads `salah.exe` as a downloadable artifact — same pattern as
the FocusLock auto-build.

## Notification sound

Drop a short `.wav` file at
`windows/salah_win/resources/sounds/adhan_beep.wav`, or pick any
`.wav`/`.mp3`/`.ogg` file via **Settings → Sound → Choose Sound File**.
`.wav` needs no extra dependency (uses the stdlib `winsound` module);
`.mp3`/`.ogg` need the optional `playsound` package from
requirements.txt.

## Autostart on login (optional)

Press `Win+R`, type `shell:startup`, and drop a shortcut to `salah.exe`
(or to `python windows/main.py` if running from source) in the folder
that opens.

## Uninstalling

Delete the exe / source folder, then remove settings and cache:

```powershell
rmdir /s /q "%APPDATA%\salah-app"
rmdir /s /q "%LOCALAPPDATA%\salah-app"
```
