"""Right-hand sidebar panel.

Composes the sidebar sections (page position, search) into one column.
New sections (e.g. page thumbnails, document outline) are added as their own
widgets in this package, without restructuring `MainWindow`'s layout — see
docs/ARCHITECTURE.md and docs/FEATURES.md.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pdfalchemy.paths import APP_ICON_PATH
from pdfalchemy.ui.sidebar.page_nav_section import PageNavSection
from pdfalchemy.ui.sidebar.search_section import SearchSection

#: Fixed-ish default width; the panel remains user-resizable via the
#: QSplitter it's placed in (see ui/main_window.py).
DEFAULT_WIDTH = 240
MINIMUM_WIDTH = 180

_SECTION_SPACING = 20


class SidebarPanel(QWidget):
    """Displays document-level status info to the right of the PDF viewer."""

    #: Emitted when the user commits an edit to the current-page field
    #: (Enter pressed or focus lost) with the requested 1-based page number,
    #: already clamped to the valid page range.
    page_jump_requested = Signal(int)

    #: Emitted on every keystroke in the search field with its current text.
    search_query_changed = Signal(str)

    #: Emitted to request jumping to the next/previous search match.
    search_next_requested = Signal()
    search_prev_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarPanel")
        self.setMinimumWidth(MINIMUM_WIDTH)
        self.resize(DEFAULT_WIDTH, self.height())

        self._page_nav = PageNavSection(self)
        self._page_nav.page_jump_requested.connect(self.page_jump_requested)

        self._search = SearchSection(self)
        self._search.query_changed.connect(self.search_query_changed)
        self._search.next_requested.connect(self.search_next_requested)
        self._search.prev_requested.connect(self.search_prev_requested)

        logo_label = QLabel(self)
        logo_label.setObjectName("sidebarLogo")
        logo_label.setPixmap(
            QPixmap(str(APP_ICON_PATH)).scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)
        layout.addWidget(self._page_nav)
        layout.addSpacing(_SECTION_SPACING)
        layout.addWidget(self._search)
        layout.addStretch(1)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def set_page_position(self, current_page: int, page_count: int) -> None:
        """Show the given 1-based current page out of ``page_count`` total."""
        self._page_nav.set_page_position(current_page, page_count)
        self._search.set_document_open(True)

    def clear(self) -> None:
        """Show the "no document open" placeholder state."""
        self._page_nav.clear()
        self._search.set_document_open(False)

    def focus_search(self) -> None:
        """Focus and select the search field's text (e.g. on Ctrl+F)."""
        self._search.focus_field()

    def update_search_results(
        self, current_match: int, total_matches: int, searching: bool
    ) -> None:
        """Update the "x of y found" label and prev/next buttons' state."""
        self._search.update_results(current_match, total_matches, searching)
