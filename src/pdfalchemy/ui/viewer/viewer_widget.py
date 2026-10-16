"""PDF page viewer widget, built on Qt's QPdfView/QPdfDocument.

Qt's `QtPdf` module is used directly here rather than through `core/`,
because `QPdfDocument` is Qt's combined document-model-and-renderer object —
wrapping it in a Qt-free abstraction would add no value at this layer. See
docs/ARCHITECTURE.md for the reasoning behind keeping `core/` Qt-free while
still allowing `ui/` to use Qt's PDF module for viewing.

This widget is a thin coordinator: zoom, search, page geometry, and the
highlight overlay each live in their own module of this package.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QVBoxLayout, QWidget

from pdfalchemy.ui.viewer.empty_state import EmptyStateView
from pdfalchemy.ui.viewer.overlays import SearchHighlightOverlay
from pdfalchemy.ui.viewer.page_layout import LayoutParams, PageLayout
from pdfalchemy.ui.viewer.search import SearchController
from pdfalchemy.ui.viewer.zoom import ZoomControl, ZoomController

_FLOAT_MARGIN = 12


class PdfViewerWidget(QWidget):
    """Displays a single PDF document using Qt's built-in PDF renderer."""

    #: Emitted whenever the current page or total page count changes.
    #: Args: ``current_page`` (1-based), ``page_count`` (0 when no document
    #: is open).
    page_position_changed = Signal(int, int)

    #: Emitted when the zoom factor changes (1.0 == 100%).
    zoom_changed = Signal(float)

    #: Emitted when the user clicks "Open PDF..." on the empty-state card.
    open_requested = Signal()

    #: Emitted when search results change.
    #: Args: ``current_match`` (1-based, 0 if none), ``total_matches``,
    #: ``searching`` (``True`` while more results may still arrive).
    search_results_changed = Signal(int, int, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pdfViewer")

        self._document = QPdfDocument(self)
        # Page geometry, rebuilt lazily. Qt's own "current page" is not
        # reliable when several pages are visible, so the page is derived
        # from this layout instead.
        self._page_layout = PageLayout()
        # Set while a programmatic jump is scrolling the view, and kept
        # afterwards until the user scrolls or zooms again: the last pages
        # may not be scrollable to the top when zoomed out, so the requested
        # page is reported instead of the one derived from the layout.
        self._jumping = False
        self._forced_page: int | None = None

        self._view = QPdfView(self)
        self._view.setDocument(self._document)
        self._view.setPageMode(QPdfView.PageMode.MultiPage)
        self._view.setZoomMode(QPdfView.ZoomMode.Custom)

        self._zoom = ZoomController(self._view, self._document, self)
        self._search = SearchController(self._document, self)

        self._empty_state = EmptyStateView(self)
        self._empty_state.open_requested.connect(self.open_requested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        layout.addWidget(self._empty_state)

        self._zoom_control = ZoomControl(self)
        self._zoom_control.zoom_in_requested.connect(self.zoom_in)
        self._zoom_control.zoom_out_requested.connect(self.zoom_out)
        self._zoom_control.reset_requested.connect(self.reset_zoom)
        self._zoom_control.set_zoom(self._zoom.zoom)
        self._zoom_control.hide()
        self._view.hide()

        self._search_overlay = SearchHighlightOverlay(
            self._view, self._search, self.page_layout, self
        )
        self._search_overlay.hide()

        self._zoom.zoom_changed.connect(self._on_zoom_changed)
        self._search.results_changed.connect(self.search_results_changed)
        self._search.match_activated.connect(self._on_match_activated)
        self._search.highlights_changed.connect(self._search_overlay.update)
        self._search.active_changed.connect(self._search_overlay.setVisible)

        self._document.pageCountChanged.connect(self._on_page_count_changed)
        self._document.statusChanged.connect(self._on_status_changed)
        self._view.verticalScrollBar().valueChanged.connect(self._on_scrolled)
        self._view.verticalScrollBar().rangeChanged.connect(self._position_zoom_control)
        self._view.horizontalScrollBar().valueChanged.connect(
            self._search_overlay.update
        )

    # -- Document ---------------------------------------------------------

    @property
    def document(self) -> QPdfDocument:
        """The underlying ``QPdfDocument`` backing this viewer."""
        return self._document

    def load(self, file_path: str) -> QPdfDocument.Error:
        """Load a PDF file for viewing.

        Returns the resulting :class:`QPdfDocument.Error` (``None_`` on
        success) so the caller can report a failure to the user.
        """
        return self._document.load(file_path)

    def close_document(self) -> None:
        """Close the currently displayed document, clearing the view."""
        self._document.close()
        self._on_page_count_changed()

    # -- Navigation -------------------------------------------------------

    def jump_to_page(self, page_number: int) -> None:
        """Scroll the view to the start (top-left) of the given page.

        ``page_number`` is 1-based and clamped to the valid page range. Does
        nothing if no document is open.
        """
        page_count = self._document.pageCount()
        if page_count <= 0:
            return

        page_index = max(0, min(page_number - 1, page_count - 1))
        self._jump_to(page_index, QPointF(0, 0))

    def _jump_to(self, page_index: int, location: QPointF) -> None:
        self._jumping = True
        try:
            self._view.pageNavigator().jump(page_index, location)
        finally:
            self._jumping = False
        self._forced_page = page_index
        self._emit_page_position()

    # -- Zoom -------------------------------------------------------------

    @property
    def zoom_factor(self) -> float:
        """Current zoom factor (1.0 == 100%)."""
        return self._zoom.zoom

    def set_zoom_factor(self, factor: float, anchor: QPointF | None = None) -> None:
        """Zoom to ``factor`` (clamped), keeping the viewport point ``anchor`` fixed.

        ``anchor`` defaults to the centre of the viewport.
        """
        self._zoom.set_zoom_factor(factor, anchor)

    def zoom_in(self) -> None:
        """Zoom to the next fixed step above the current zoom."""
        self._zoom.zoom_in()

    def zoom_out(self) -> None:
        """Zoom to the next fixed step below the current zoom."""
        self._zoom.zoom_out()

    def reset_zoom(self) -> None:
        """Return to 100%."""
        self._zoom.reset_zoom()

    def _on_zoom_changed(self, factor: float) -> None:
        self._forced_page = None
        self._zoom_control.set_zoom(factor)
        self.zoom_changed.emit(factor)
        self._emit_page_position()
        self._search_overlay.update()

    # -- Search -----------------------------------------------------------

    def set_search_query(self, text: str) -> None:
        """Queue a debounced search for ``text`` (see :class:`SearchController`)."""
        self._search.set_query(text)

    def clear_search(self) -> None:
        """Stop/clear any search and remove its highlights immediately."""
        self._search.clear()

    def search_next(self) -> None:
        """Jump to the next match, wrapping around after the last one."""
        self._search.next()

    def search_prev(self) -> None:
        """Jump to the previous match, wrapping around before the first one."""
        self._search.previous()

    def _on_match_activated(self, page_index: int, location: QPointF) -> None:
        self._jump_to(page_index, location)

    # -- Page geometry ----------------------------------------------------

    def page_layout(self) -> PageLayout:
        """The page geometry for the current zoom and viewport, rebuilt if stale."""
        margins = self._view.documentMargins()
        params = LayoutParams(
            dpi_x=self.logicalDpiX(),
            dpi_y=self.logicalDpiY(),
            scale=self._zoom.total_scale,
            margin_left=margins.left(),
            margin_right=margins.right(),
            margin_top=margins.top(),
            page_spacing=self._view.pageSpacing(),
            viewport_width=self._view.viewport().width(),
        )
        if not self._page_layout.matches(params):
            sizes = [
                (size.width(), size.height())
                for size in (
                    self._document.pagePointSize(index)
                    for index in range(self._document.pageCount())
                )
            ]
            self._page_layout.rebuild(sizes, params)
        return self._page_layout

    def _emit_page_position(self, *_args: object) -> None:
        page_count = self._document.pageCount()
        if page_count <= 0:
            self.page_position_changed.emit(1, 0)
            return

        if self._forced_page is not None:
            page_index = self._forced_page
        else:
            scroll_bar = self._view.verticalScrollBar()
            page_index = self.page_layout().visible_page_index(
                scroll_bar.value(), self._view.viewport().height(), scroll_bar.maximum()
            )
        self.page_position_changed.emit(page_index + 1, page_count)

    # -- Qt event handlers & state changes --------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_zoom_control()
        self._position_search_overlay()

    def _position_zoom_control(self, *_args: object) -> None:
        control = self._zoom_control
        control.adjustSize()
        viewport_right = self._view.viewport().geometry().right()
        control.move(viewport_right - control.width() - _FLOAT_MARGIN, _FLOAT_MARGIN)
        control.raise_()

    def _position_search_overlay(self) -> None:
        viewport_rect = self._view.viewport().geometry()
        top_left = self._view.mapTo(self, viewport_rect.topLeft())
        self._search_overlay.setGeometry(
            top_left.x(), top_left.y(), viewport_rect.width(), viewport_rect.height()
        )
        self._search_overlay.raise_()

    def _on_status_changed(self, status: QPdfDocument.Status) -> None:
        # A new document was just loaded or the previous one closed — any
        # search results/highlights refer to content that's gone now.
        self.clear_search()
        if status == QPdfDocument.Status.Ready:
            self._zoom.fit_to_width()
        self._on_page_count_changed()

    def _on_page_count_changed(self, *_args: object) -> None:
        has_document = self._document.pageCount() > 0

        self._page_layout.invalidate()
        self._forced_page = None
        self._zoom_control.setVisible(has_document)
        self._view.setVisible(has_document)
        self._empty_state.setVisible(not has_document)
        if not has_document:
            # QPdfView doesn't recompute its (now empty) scroll range on its
            # own when the document is closed, leaving the previous page's
            # scrollbar and rendering stuck on screen; toggling the zoom
            # mode forces it to re-layout against the empty document.
            self._view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            self._view.setZoomMode(QPdfView.ZoomMode.Custom)
        self._position_zoom_control()
        self._position_search_overlay()
        self._emit_page_position()

    def _on_scrolled(self, _value: int) -> None:
        if not self._jumping:
            self._forced_page = None
        self._emit_page_position()
        self._search_overlay.update()
