"""Transparent overlay drawing search-match boxes on top of the page view."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QWidget

from pdfalchemy.ui.theme import Colors
from pdfalchemy.ui.viewer.page_layout import PageLayout
from pdfalchemy.ui.viewer.search import SearchController

#: Highlight styling for search matches (semi-transparent fill + border),
#: painted directly rather than via QSS since they're drawn on the page
#: canvas, not a styled widget.
_MATCH_FILL = QColor(255, 213, 79, 90)
_MATCH_BORDER = QColor(255, 193, 7, 200)


def _accent(alpha: int) -> QColor:
    color = QColor(Colors.ACCENT_DEFAULT)
    color.setAlpha(alpha)
    return color


_CURRENT_MATCH_FILL = _accent(110)
_CURRENT_MATCH_BORDER = _accent(230)


class SearchHighlightOverlay(QWidget):
    """Draws a box over every search match on the currently visible pages."""

    def __init__(
        self,
        view: QPdfView,
        search: SearchController,
        page_layout: Callable[[], PageLayout],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._search = search
        self._page_layout = page_layout
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)

    def paintEvent(self, _event: QPaintEvent) -> None:
        if self._search.count <= 0:
            return

        layout = self._page_layout()
        scroll_y = self._view.verticalScrollBar().value()
        scroll_x = self._view.horizontalScrollBar().value()
        bottom = scroll_y + self._view.viewport().height()

        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        for page_index in layout.pages_in_range(scroll_y, bottom):
            for match in self._search.results_on_page(page_index):
                rects = match.rectangles()
                is_current = self._search.is_current_match(page_index, rects)
                painter.setBrush(_CURRENT_MATCH_FILL if is_current else _MATCH_FILL)
                painter.setPen(_CURRENT_MATCH_BORDER if is_current else _MATCH_BORDER)
                for rect in rects:
                    x, y, width, height = layout.page_rect_to_content(
                        page_index, rect.x(), rect.y(), rect.width(), rect.height()
                    )
                    painter.drawRect(QRectF(x - scroll_x, y - scroll_y, width, height))
