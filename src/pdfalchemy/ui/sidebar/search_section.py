"""Sidebar section with the find-in-document field and match navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _SearchLineEdit(QLineEdit):
    """QLineEdit distinguishing Enter from Shift+Enter for search navigation."""

    next_requested = Signal()
    prev_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.prev_requested.emit()
            else:
                self.next_requested.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self.text():
            self.clear()
            event.accept()
            return
        super().keyPressEvent(event)


class SearchSection(QWidget):
    """Search field, "x of y" result label, and previous/next buttons."""

    #: Emitted on every keystroke in the search field with its current text.
    query_changed = Signal(str)

    #: Emitted to request jumping to the next/previous search match.
    next_requested = Signal()
    prev_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document_open = False

        heading_label = QLabel("Search", self)
        heading_label.setObjectName("sidebarHeading")

        self._search_edit = _SearchLineEdit(self)
        self._search_edit.setObjectName("searchEdit")
        self._search_edit.setPlaceholderText("Find in document...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._handle_text_changed)
        self._search_edit.next_requested.connect(self.next_requested)
        self._search_edit.prev_requested.connect(self.prev_requested)

        self._result_label = QLabel(self)
        self._result_label.setObjectName("searchResultLabel")

        self._prev_button = QPushButton("\u2191", self)
        self._prev_button.setObjectName("searchPrevButton")
        self._prev_button.setToolTip("Previous match (Shift+Enter)")
        self._prev_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._prev_button.clicked.connect(self.prev_requested)

        self._next_button = QPushButton("\u2193", self)
        self._next_button.setObjectName("searchNextButton")
        self._next_button.setToolTip("Next match (Enter)")
        self._next_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._next_button.clicked.connect(self.next_requested)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(4)
        nav_row.addWidget(self._result_label, 1)
        nav_row.addWidget(self._prev_button)
        nav_row.addWidget(self._next_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(heading_label)
        layout.addWidget(self._search_edit)
        layout.addLayout(nav_row)

        self.set_document_open(False)

    def set_document_open(self, document_open: bool) -> None:
        """Show the section while a document is open; reset and hide it otherwise."""
        self._document_open = document_open
        if not document_open:
            self._search_edit.clear()
            self.update_results(0, 0, False)
        self.setVisible(document_open)

    def focus_field(self) -> None:
        """Focus and select the search field's text (e.g. on Ctrl+F)."""
        if self._document_open:
            self._search_edit.setFocus()
            self._search_edit.selectAll()

    def update_results(
        self, current_match: int, total_matches: int, searching: bool
    ) -> None:
        """Update the "x of y found" label and prev/next buttons' state."""
        if total_matches <= 0:
            if searching:
                text = "Searching..."
            elif self._search_edit.text().strip():
                text = "No matches"
            else:
                text = ""
        else:
            text = f"{current_match} of {total_matches}" + ("..." if searching else "")
        self._result_label.setText(text)
        self._prev_button.setEnabled(total_matches > 0)
        self._next_button.setEnabled(total_matches > 0)

    def _handle_text_changed(self, text: str) -> None:
        if self._document_open:
            self.query_changed.emit(text)
