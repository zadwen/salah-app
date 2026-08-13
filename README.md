# Salah — Islamic Prayer Times for Linux

A lightweight, native system-tray app that shows all five daily prayer
times, reminds you before each one, and always displays the next
prayer + countdown in your taskbar. Built with Python 3 and GTK3
(AppIndicator3), so it feels native on Ubuntu, Zorin OS, Arch, Fedora,
and most other Linux desktops — no Electron, no heavy runtime.

## Features

- **All 5 daily prayers** (Fajr, Dhuhr, Asr, Maghrib, Isha) + Sunrise, computed
  for your location via the [Aladhan API](https://aladhan.com/prayer-times-api).
- **Tray/taskbar widget**: the indicator label always shows the next
  prayer and a live countdown (e.g. `Dhuhr 1h 12m`), updated every 30s.
- **Reminders**: configurable "N minutes before" notification, plus an
  optional notification exactly at prayer time, with sound.
- **Qibla direction**: computed via great-circle bearing to the Kaaba,
  shown on a simple compass widget.
- **Hijri date**: pulled straight from the API alongside the Gregorian date.
- **Bilingual UI**: English / Arabic, switchable in Settings (including
  RTL-friendly Arabic prayer names and countdown strings).
- **Configurable calculation method**: ISNA, MWL, Umm al-Qura, Egyptian,
  Karachi, and more (Aladhan method IDs).
- **Lightweight**: pure Python stdlib for networking (`urllib`, no
  `requests`/pip dependency), a single background thread, GLib timers
  instead of busy loops, and daily on-disk caching so it only calls
  the API once per day per location.

## How it works (architecture)

```
salah-app/
├── main.py                    # entry point
├── salah_app/
│   ├── api.py                 # Aladhan API client + IP geolocation, disk cache
│   ├── config.py              # JSON config load/save (~/.config/salah-app/)
│   ├── constants.py           # calculation methods, Kaaba coords, prayer order
│   ├── i18n.py                # English/Arabic string tables
│   ├── qibla.py                # great-circle bearing + distance to Kaaba
│   ├── qibla_window.py        # compass widget (GTK DrawingArea)
│   ├── scheduler.py           # day-plan / next-prayer / countdown logic (no GTK)
│   ├── settings_dialog.py     # GTK settings dialog
│   ├── notifier.py            # libnotify wrapper + sound playback
│   ├── tray.py                # AppIndicator3 tray app, ties everything together
│   └── resources/
│       ├── icons/salah-app.svg
│       └── sounds/            # put your adhan/beep sound file here
├── install.sh                 # multi-distro installer
├── salah-app.desktop
└── requirements.txt
```

The GTK/AppIndicator layer (`tray.py`) is kept separate from the pure
logic (`scheduler.py`, `qibla.py`, `api.py`) so the scheduling and
calculation code can be unit-tested without a display server.

Networking runs on a background thread; all UI updates happen via
`GLib.idle_add` back on the main thread, so the tray never freezes
while fetching prayer times.

## Installation

### Option 1: automated installer (recommended)

```bash
git clone <this-repo-url> salah-app   # or unzip the provided archive
cd salah-app
chmod +x install.sh
./install.sh
```

The script detects your package manager (`apt`, `pacman`, `dnf`, or
`zypper`) and installs the needed system packages:

- `python3`, `python3-gi` (PyGObject) + GTK3 typelib
- `gir1.2-notify-0.7` (libnotify bindings, for desktop notifications)
- AppIndicator: `gir1.2-ayatanaappindicator3-0.1` (or the classic
  `appindicator3` package if Ayatana isn't packaged on your distro)
- `pulseaudio-utils` (`paplay`) or `alsa-utils` (`aplay`) for reminder sounds

It then copies the app to `~/.local/share/salah-app`, creates a
launcher at `~/.local/bin/salah-app`, installs a `.desktop` entry so
"Salah" shows up in your app menu, and optionally adds it to autostart.

### Option 2: manual install

```bash
# Ubuntu / Zorin / Debian
sudo apt-get install python3 python3-gi gir1.2-gtk-3.0 gir1.2-notify-0.7 \
    gir1.2-ayatanaappindicator3-0.1 pulseaudio-utils

# Arch / Manjaro
sudo pacman -S python python-gobject gtk3 libnotify libayatana-appindicator

# Fedora
sudo dnf install python3-gobject gtk3 libnotify libayatana-appindicator3
```

Then just run it in place:

```bash
python3 main.py
```

> **Note on AppIndicator in GNOME:** stock GNOME (used by some Zorin/Fedora
> setups) doesn't show tray icons out of the box. Install the
> [AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/)
> GNOME Shell extension. Cinnamon, XFCE, KDE Plasma, and MATE all support
> tray icons natively — no extra extension needed there.

## Usage

- Click the tray icon to see the dropdown: current next-prayer countdown,
  today's full schedule, Hijri date, Qibla direction, Settings, Refresh, Quit.
- **Settings** lets you set: language, calculation method, manual vs.
  auto (IP-based) location, reminder on/off + minutes-before, notify-at-time
  on/off, and a custom sound file.
- Location auto-detection uses IP geolocation (no GPS needed) — accurate
  enough for prayer-time calculation, but you can enter exact
  latitude/longitude manually in Settings for precision.
- Prayer times are cached on disk for the day, so the app is efficient
  even if you leave it running for weeks; it re-fetches once per new day
  or when you hit "Refresh Now".

## Adding a custom notification sound

Drop an `.ogg`/`.wav`/`.mp3` file anywhere on disk and select it via
**Settings → Sound → Choose Sound File**. If you don't set one, the app
looks for `salah_app/resources/sounds/adhan_beep.ogg` — add your own
short beep/adhan clip there (not bundled here for licensing reasons).

## Resource usage

- Idle CPU: effectively 0% — the app only wakes every 30 seconds via a
  GLib timer to refresh the countdown label, and performs a single
  cheap datetime comparison to decide if a notification is due.
  Network calls happen once per day.
- Memory: a Python/GTK process, typically in the 25–40 MB range, in
  line with other native GTK tray utilities.

## Uninstalling

```bash
rm -rf ~/.local/share/salah-app ~/.local/bin/salah-app
rm -f ~/.local/share/applications/salah-app.desktop
rm -f ~/.config/autostart/salah-app.desktop
rm -rf ~/.config/salah-app ~/.cache/salah-app   # also removes your settings
```

## Roadmap ideas (not implemented)

- GNOME Shell / Cinnamon applet variants for tighter panel integration
- Monthly calendar view / printable prayer timetable
- Multiple saved locations (e.g. home + work)
- Adhan audio playback (full call to prayer, not just a beep)

## License

MIT — do whatever you like with it.
