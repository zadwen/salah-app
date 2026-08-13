#!/usr/bin/env python3
"""Entry point for the Salah prayer-times tray app."""
import sys

try:
    from salah_app.tray import SalahApp
except ImportError as e:
    sys.stderr.write(
        "Failed to import salah_app. Make sure PyGObject and the "
        "AppIndicator3/AyatanaAppIndicator3 GObject introspection "
        "bindings are installed (see README.md).\n"
        f"Original error: {e}\n"
    )
    sys.exit(1)


def main():
    app = SalahApp()
    app.run()


if __name__ == "__main__":
    main()
