"""Design tokens and theme application for the dark/deep-purple UI.

`Colors` mirrors the palette documented in docs/DESIGN.md, for the rare
cases where Python code needs a color value directly (e.g. a custom-painted
widget) rather than through the QSS stylesheet. `apply_theme()` loads and
applies the stylesheet itself.

Keep this module, docs/DESIGN.md, and resources/styles/dark.qss in sync.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

_STYLES_DIR = Path(__file__).resolve().parent.parent / "resources" / "styles"
_DEFAULT_STYLESHEET = _STYLES_DIR / "dark.qss"


class Colors:
    """Hex values for the design tokens defined in docs/DESIGN.md."""

    # Surfaces
    SURFACE_0 = "#121214"
    SURFACE_1 = "#1A1A1D"
    SURFACE_2 = "#242428"
    SURFACE_3 = "#2D2D33"
    BORDER = "#302F36"

    # Text
    TEXT_PRIMARY = "#F2F1F5"
    TEXT_SECONDARY = "#A4A3AD"
    TEXT_DISABLED = "#5A5960"

    # Accent (deep purple)
    ACCENT_DEFAULT = "#7C3AED"
    ACCENT_HOVER = "#8B5CF6"
    ACCENT_PRESSED = "#6D28D9"
    ACCENT_MUTED = "rgba(124, 58, 237, 0.16)"

    # Semantic
    STATUS_SUCCESS = "#22C55E"
    STATUS_WARNING = "#F59E0B"
    STATUS_DANGER = "#EF4444"
    STATUS_INFO = "#38BDF8"


def apply_theme(app: QApplication, stylesheet_path: Path = _DEFAULT_STYLESHEET) -> None:
    """Load the given QSS file and apply it to the whole application."""
    app.setStyleSheet(stylesheet_path.read_text(encoding="utf-8"))
