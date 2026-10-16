"""QApplication setup and startup wiring."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from pdfalchemy.paths import APP_ICON_PATH
from pdfalchemy.ui.main_window import MainWindow
from pdfalchemy.ui.theme import apply_theme

# Must match AppUserModelID in installer/pdfalchemy.iss so shortcuts and the
# taskbar group under the same identity (and show the app icon, not python's).
_APP_USER_MODEL_ID = "PDFAlchemy.PDFAlchemy"


def _set_windows_app_id() -> None:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_USER_MODEL_ID)


def _pdf_path_from_args(args: list[str]) -> str | None:
    """Return the first command-line argument that is an existing file."""
    for arg in args:
        if Path(arg).is_file():
            return str(Path(arg).resolve())
    return None


def run() -> int:
    """Create the QApplication, show the main window, and run the event loop.

    Returns the process exit code from the Qt event loop.
    """
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Alchemy")
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    apply_theme(app)

    window = MainWindow()
    window.show()

    # Windows launches "PDFAlchemy.exe <file>" for double-click / "Open with".
    if file_path := _pdf_path_from_args(app.arguments()[1:]):
        window.open_path(file_path)

    return app.exec()
