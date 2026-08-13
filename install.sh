#!/usr/bin/env bash
# Installer for the Salah prayer-times tray app.
# Supports apt (Ubuntu/Zorin/Debian), pacman (Arch/Manjaro),
# dnf (Fedora), and zypper (openSUSE).
set -euo pipefail

APP_NAME="salah-app"
INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
AUTOSTART_DIR="${HOME}/.config/autostart"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Salah App installer =="

install_deps() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "-> Detected apt (Debian/Ubuntu/Zorin)"
        sudo apt-get update
        sudo apt-get install -y \
            python3 python3-gi gir1.2-gtk-3.0 \
            gir1.2-notify-0.7 \
            gir1.2-ayatanaappindicator3-0.1 || \
        sudo apt-get install -y gir1.2-appindicator3-0.1
        # sound playback fallback tools
        sudo apt-get install -y pulseaudio-utils || sudo apt-get install -y alsa-utils

    elif command -v pacman >/dev/null 2>&1; then
        echo "-> Detected pacman (Arch/Manjaro)"
        sudo pacman -Sy --needed --noconfirm \
            python python-gobject gtk3 libnotify \
            libayatana-appindicator || \
        sudo pacman -Sy --needed --noconfirm libappindicator-gtk3
        sudo pacman -Sy --needed --noconfirm pulseaudio-alsa alsa-utils || true

    elif command -v dnf >/dev/null 2>&1; then
        echo "-> Detected dnf (Fedora/Nobara)"
        sudo dnf install -y \
            python3 python3-gobject gtk3 libnotify \
            libayatana-appindicator3 || \
        sudo dnf install -y libappindicator-gtk3
        sudo dnf install -y pulseaudio-utils || true

    elif command -v zypper >/dev/null 2>&1; then
        echo "-> Detected zypper (openSUSE)"
        sudo zypper install -y \
            python3 python3-gobject python3-gobject-Gdk typelib-1_0-Gtk-3_0 \
            libnotify-tools typelib-1_0-AyatanaAppIndicator3-0_1 || true

    else
        echo "!! Could not detect a supported package manager."
        echo "   Please install manually: python3, PyGObject (GTK3 bindings)," 
        echo "   libnotify, and AppIndicator3 or AyatanaAppIndicator3 typelibs."
    fi
}

install_deps

echo "-> Copying app files to ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cp -r "${SCRIPT_DIR}/salah_app" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/main.py" "${INSTALL_DIR}/"

echo "-> Creating launcher at ${BIN_DIR}/${APP_NAME}"
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/${APP_NAME}" <<EOF
#!/usr/bin/env bash
cd "${INSTALL_DIR}"
exec python3 main.py "\$@"
EOF
chmod +x "${BIN_DIR}/${APP_NAME}"

echo "-> Installing .desktop entry"
mkdir -p "${DESKTOP_DIR}"
cat > "${DESKTOP_DIR}/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Salah
Comment=Islamic prayer times, reminders, Qibla and Hijri date
Exec=${BIN_DIR}/${APP_NAME}
Icon=${INSTALL_DIR}/salah_app/resources/icons/salah-app.svg
Terminal=false
Categories=Utility;Religion;
X-GNOME-UsesNotifications=true
EOF

read -r -p "Start Salah automatically at login? [Y/n] " reply
reply=${reply:-Y}
if [[ "$reply" =~ ^[Yy]$ ]]; then
    mkdir -p "${AUTOSTART_DIR}"
    cp "${DESKTOP_DIR}/${APP_NAME}.desktop" "${AUTOSTART_DIR}/${APP_NAME}.desktop"
    echo "-> Autostart entry added."
fi

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo
    echo "NOTE: ${BIN_DIR} is not on your PATH."
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo
echo "Installation complete. Launch with: ${APP_NAME}"
echo "Or find 'Salah' in your applications menu (may need a logout/login"
echo "for the menu entry to appear on some desktop environments)."
