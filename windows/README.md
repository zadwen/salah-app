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
  mutes notification sound instantly — including a sound that's
  already playing when you hit it, not just future ones. Every
  notification banner also has an "✕" to close it on demand, which
  stops its sound too. Muting never hides the notification itself —
  you still see it, it's just silent.
- **Run at Windows startup.** A toggle in Settings adds the app to
  your per-user login items (registry Run key, no admin rights
  needed). When launched this way it starts minimized straight to the
  tray instead of popping the window open.
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

## Publishing an easy download for other people

A GitHub Actions workflow (`.github/workflows/build-windows.yml`)
builds `salah.exe` automatically on every push to `windows/` or
`salah_app/` (uploaded as an Actions artifact — requires a GitHub
login to grab).

For a link anyone can click with no login, push a version tag instead:

```bash
git tag v1.0.0
git push --tags
```

That triggers the same build, then attaches `salah.exe` directly to a
GitHub Release on your repo — the download link looks like:
`github.com/zadwen/salah-app/releases/latest`, and works for anyone,
signed in or not. Bump the tag (`v1.0.1`, `v1.1.0`, ...) each time you
want to publish a new build.

## Autostart on login

Turn on **Settings → Run when Windows starts**. This adds a per-user
registry entry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
pointing at the exe (or `pythonw main.py` if running from source) —
no admin rights required, and it's removed the moment you flip the
toggle off. When launched this way, the app starts minimized to the
tray instead of opening the window every login.

Alternative (equivalent, no toggle needed): press `Win+R`, type
`shell:startup`, and drop a shortcut to `salah.exe` in the folder that
opens.

## Notification sound

Drop a short `.wav`, `.mp3`, or `.ogg` file at
`windows/salah_win/resources/sounds/adhan_beep.wav`, or pick one via
**Settings → Sound → Choose Sound File**. Playback goes through
`pygame.mixer`, which — unlike a fire-and-forget player — can actually
be stopped mid-playback: hitting Mute or closing a notification banner
cuts the sound off immediately instead of letting it run to the end
in the background.

## Autostart on login (optional)

Press `Win+R`, type `shell:startup`, and drop a shortcut to `salah.exe`
(or to `python windows/main.py` if running from source) in the folder
that opens.

(Or just use **Settings → Run when Windows starts** inside the app — see above.)

## Uninstalling

Delete the exe / source folder, then remove settings and cache:

```powershell
rmdir /s /q "%APPDATA%\salah-app"
rmdir /s /q "%LOCALAPPDATA%\salah-app"
```
