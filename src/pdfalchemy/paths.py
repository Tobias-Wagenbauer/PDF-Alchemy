"""Locations of bundled resource files (works from source and PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    _PACKAGE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "pdfalchemy"
else:
    _PACKAGE_DIR = Path(__file__).resolve().parent

RESOURCES_DIR = _PACKAGE_DIR / "resources"
APP_ICON_PATH = RESOURCES_DIR / "icons" / "app.png"
