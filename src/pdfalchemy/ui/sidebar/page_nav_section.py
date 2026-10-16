"""Sidebar section showing and editing the current page position."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget


class PageNavSection(QWidget):
    """Current/total page indicator whose current-page field is editable."""

    #: Emitted when the user commits an edit to the current-page field
    #: (Enter pressed or focus lost) with the requested 1-based page number,
    #: already clamped to the valid page range.
    page_jump_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._page_count = 0

        heading_label = QLabel("Pages", self)
        heading_label.setObjectName("sidebarHeading")

        self._current_page_edit = QLineEdit(self)
        self._current_page_edit.setObjectName("currentPageEdit")
        self._current_page_edit.setFrame(False)
        self._current_page_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._current_page_edit.setValidator(QIntValidator(1, 1, self))
        self._current_page_edit.setFixedWidth(72)
        self._current_page_edit.editingFinished.connect(self._handle_edit_finished)

        self._total_pages_label = QLabel(self)
        self._total_pages_label.setObjectName("totalPagesLabel")

        self._no_document_label = QLabel("No document open", self)
        self._no_document_label.setObjectName("noDocumentLabel")
        self._no_document_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(heading_label)
        layout.addWidget(self._current_page_edit)
        layout.addWidget(self._total_pages_label)
        layout.addWidget(self._no_document_label)

        self.clear()

    def set_page_position(self, current_page: int, page_count: int) -> None:
        """Show the given 1-based current page out of ``page_count`` total."""
        self._page_count = page_count
        self._current_page_edit.validator().setRange(1, page_count)

        # Don't clobber in-progress user input if a scroll-driven update
        # arrives while the field is focused.
        if not self._current_page_edit.hasFocus():
            self._current_page_edit.setText(str(current_page))

        self._total_pages_label.setText(f"of {page_count}")
        self._current_page_edit.setVisible(True)
        self._total_pages_label.setVisible(True)
        self._no_document_label.setVisible(False)

    def clear(self) -> None:
        """Show the "no document open" placeholder state."""
        self._page_count = 0
        self._current_page_edit.clear()
        self._current_page_edit.setVisible(False)
        self._total_pages_label.setVisible(False)
        self._no_document_label.setVisible(True)

    def _handle_edit_finished(self) -> None:
        if self._page_count <= 0:
            return

        try:
            page_number = int(self._current_page_edit.text().strip())
        except ValueError:
            # Invalid/empty input: leave the current page untouched.
            return

        page_number = max(1, min(page_number, self._page_count))
        self._current_page_edit.setText(str(page_number))
        self.page_jump_requested.emit(page_number)
