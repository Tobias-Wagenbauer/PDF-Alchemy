"""Document text search: debounced query handling and match navigation.

Wraps Qt's asynchronous ``QPdfSearchModel`` and owns the "current match"
state. It knows nothing about scrolling or painting: it announces the match
to show via signals and exposes the results for whoever paints highlights.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QRectF, QSizeF, QTimer, Signal
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel

#: Minimum query length before an auto-search is triggered.
MIN_SEARCH_CHARS = 3
#: Debounce delay (ms) after the last keystroke before searching.
_SEARCH_DEBOUNCE_MS = 250


class SearchController(QObject):
    """Debounced search over a ``QPdfDocument`` with next/previous navigation."""

    #: Emitted when search results change.
    #: Args: ``current_match`` (1-based, 0 if none), ``total_matches``,
    #: ``searching`` (``True`` while more results may still arrive).
    results_changed = Signal(int, int, bool)

    #: Emitted when a match becomes the current one and should be scrolled
    #: into view. Args: 0-based ``page_index`` and the bounding rectangle of
    #: the match (in page points).
    match_activated = Signal(int, QRectF)

    #: Emitted whenever highlight painting needs to be refreshed.
    highlights_changed = Signal()

    #: Emitted with ``True`` when a search starts and ``False`` when it is cleared.
    active_changed = Signal(bool)

    def __init__(self, document: QPdfDocument, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = QPdfSearchModel(self)
        self._model.setDocument(document)
        self._model.countChanged.connect(self._on_model_changed)
        self._model.statusChanged.connect(self._on_model_changed)

        self._pending_text = ""
        self._current_index = -1
        self._current_page: int | None = None
        self._current_rects: list[QRectF] = []

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_SEARCH_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._apply_pending)

    @property
    def count(self) -> int:
        """Number of matches found so far."""
        return self._model.count()

    def results_on_page(self, page_index: int) -> list:
        """The ``QPdfLink`` matches on the given 0-based page."""
        return self._model.resultsOnPage(page_index)

    def is_current_match(self, page_index: int, rectangles: list[QRectF]) -> bool:
        """Whether the match with ``rectangles`` on ``page_index`` is the current one."""
        return page_index == self._current_page and rectangles == self._current_rects

    def set_query(self, text: str) -> None:
        """Queue a search for ``text``.

        The actual search only starts a short debounce delay after the last
        call, and only once ``text`` is at least :data:`MIN_SEARCH_CHARS`
        long — otherwise any in-progress search is cleared.
        """
        self._pending_text = text
        self._debounce.start()

    def clear(self) -> None:
        """Stop/clear any search immediately."""
        self._debounce.stop()
        self._pending_text = ""
        self._clear_state()

    def next(self) -> None:
        """Activate the next match, wrapping around after the last one."""
        self._step(1)

    def previous(self) -> None:
        """Activate the previous match, wrapping around before the first one."""
        self._step(-1)

    def _reset_current(self) -> None:
        self._current_index = -1
        self._current_page = None
        self._current_rects = []

    def _apply_pending(self) -> None:
        text = self._pending_text.strip()
        if len(text) < MIN_SEARCH_CHARS:
            self._clear_state()
            return

        self._reset_current()
        self._model.setSearchString(text)
        self.active_changed.emit(True)
        self.highlights_changed.emit()

    def _clear_state(self) -> None:
        self._model.setSearchString("")
        self._reset_current()
        self.active_changed.emit(False)
        self.results_changed.emit(0, 0, False)

    def _step(self, direction: int) -> None:
        count = self._model.count()
        if count <= 0:
            return
        if self._current_index < 0:
            new_index = 0
        else:
            new_index = (self._current_index + direction) % count
        self._activate(new_index)

    def _activate(self, index: int) -> None:
        result = self._model.resultAtIndex(index)
        if not result.isValid():
            return

        self._current_index = index
        self._current_page = result.page()
        self._current_rects = list(result.rectangles())
        bounds = QRectF()
        for rect in self._current_rects:
            bounds = bounds.united(rect) if bounds.isValid() else QRectF(rect)
        if not bounds.isValid():
            bounds = QRectF(result.location(), QSizeF(0, 0))
        self.match_activated.emit(result.page(), bounds)
        self.highlights_changed.emit()
        self._emit_results()

    def _on_model_changed(self, *_args: object) -> None:
        count = self._model.count()
        if count > 0 and self._current_index < 0:
            # Jump to the first match as soon as any are found, rather than
            # waiting for the (possibly long) full search to finish.
            self._activate(0)
            return
        if self._current_index >= count:
            self._current_index = count - 1 if count > 0 else -1
        self.highlights_changed.emit()
        self._emit_results()

    def _emit_results(self) -> None:
        count = self._model.count()
        searching = self._model.status() == QPdfSearchModel.Status.Searching
        display_index = self._current_index + 1 if self._current_index >= 0 else 0
        self.results_changed.emit(display_index, count, searching)
