"""Manage the Windows 'launch at login' entry.

Uses the per-user Run registry key (HKCU\\...\\CurrentVersion\\Run) via
QSettings in native format, so no admin rights are needed. The app is
launched with --hidden so it starts quietly in the tray.
"""

import os
import sys

from PySide6.QtCore import QSettings

_RUN_KEY = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "SpotifyFloatingLyrics"


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        # Packaged exe: sys.executable is our exe.
        return f'"{sys.executable}" --hidden'
    # Running from source: launch the interpreter with this script.
    script = os.path.abspath(sys.argv[0])
    return f'"{sys.executable}" "{script}" --hidden'


def _run_settings() -> QSettings:
    return QSettings(_RUN_KEY, QSettings.NativeFormat)


def is_enabled() -> bool:
    return _run_settings().value(_APP_NAME) is not None


def set_enabled(enabled: bool):
    settings = _run_settings()
    if enabled:
        settings.setValue(_APP_NAME, _launch_command())
    else:
        settings.remove(_APP_NAME)
    settings.sync()
