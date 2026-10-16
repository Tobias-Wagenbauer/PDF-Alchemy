"""End-to-end smoke test of the viewer + sidebar through ``MainWindow``.

Exercises the public behaviour (open, page tracking, jump, zoom, search,
close) so structural refactors of the UI layer can be verified headlessly.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QLineEdit
from reportlab.pdfgen import canvas

from pdfalchemy.ui.main_window import MainWindow
from pdfalchemy.ui.viewer.overlays import SearchHighlightOverlay
from pdfalchemy.ui.viewer.viewer_widget import PdfViewerWidget

PAGE_COUNT = 5
SEARCH_PAGES = (1, 3)  # 0-based pages containing the search term


@pytest.fixture
def sample_pdf(tmp_path):
    path = tmp_path / "sample.pdf"
    pdf = canvas.Canvas(str(path))
    for index in range(PAGE_COUNT):
        pdf.drawString(100, 700, f"Page number {index + 1}")
        if index in SEARCH_PAGES:
            pdf.drawString(100, 650, "The alchemy of documents")
        pdf.showPage()
    pdf.save()
    return str(path)


@pytest.fixture
def window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    return win


def _last(positions):
    return positions[-1]


def test_open_jump_and_close(qtbot, window, sample_pdf):
    positions = []
    window._viewer.page_position_changed.connect(lambda c, n: positions.append((c, n)))

    window.open_path(sample_pdf)
    assert _last(positions) == (1, PAGE_COUNT)

    window._viewer.jump_to_page(3)
    assert _last(positions) == (3, PAGE_COUNT)

    # Out-of-range requests are clamped.
    window._viewer.jump_to_page(99)
    assert _last(positions) == (PAGE_COUNT, PAGE_COUNT)

    window._handle_close()
    assert _last(positions) == (1, 0)
    assert not window.close_action.isEnabled()


def test_sidebar_page_jump(qtbot, window, sample_pdf):
    positions = []
    window._viewer.page_position_changed.connect(lambda c, n: positions.append((c, n)))
    window.open_path(sample_pdf)

    window._sidebar.page_jump_requested.emit(2)
    assert _last(positions) == (2, PAGE_COUNT)


def test_zoom(qtbot, window, sample_pdf):
    window.open_path(sample_pdf)
    viewer = window._viewer
    assert viewer.zoom_factor == pytest.approx(1.0)

    viewer.zoom_in()
    assert viewer.zoom_factor == pytest.approx(1.25)
    viewer.zoom_out()
    viewer.zoom_out()
    assert viewer.zoom_factor == pytest.approx(0.75)
    viewer.reset_zoom()
    assert viewer.zoom_factor == pytest.approx(1.0)

    viewer.set_zoom_factor(100.0)
    assert viewer.zoom_factor == pytest.approx(5.0)


def test_search_next_prev_and_clear(qtbot, window, sample_pdf):
    results = []
    window._viewer.search_results_changed.connect(
        lambda i, n, s: results.append((i, n, s))
    )
    positions = []
    window._viewer.page_position_changed.connect(lambda c, n: positions.append((c, n)))
    window.open_path(sample_pdf)

    window._viewer.set_search_query("alchemy")
    qtbot.waitUntil(
        lambda: results and results[-1][1] == len(SEARCH_PAGES) and not results[-1][2]
    )
    # The first match is activated automatically and scrolled into view.
    assert results[-1][0] == 1
    assert _last(positions)[0] == SEARCH_PAGES[0] + 1

    window._viewer.search_next()
    assert results[-1][0] == 2
    assert _last(positions)[0] == SEARCH_PAGES[1] + 1

    window._viewer.search_next()  # wraps around
    assert results[-1][0] == 1

    window._viewer.search_prev()  # wraps backwards
    assert results[-1][0] == 2

    window._viewer.clear_search()
    assert results[-1] == (0, 0, False)


def test_zoomed_search_scrolls_the_match_into_the_viewport(qtbot, window, sample_pdf):
    results = []
    window._viewer.search_results_changed.connect(
        lambda i, n, s: results.append((i, n, s))
    )
    window.open_path(sample_pdf)
    viewer = window._viewer
    viewer.set_zoom_factor(3.0)
    viewer.set_search_query("alchemy")
    qtbot.waitUntil(
        lambda: results and results[-1][1] == len(SEARCH_PAGES) and not results[-1][2]
    )

    for _ in range(len(SEARCH_PAGES)):
        match = viewer._search.results_on_page(viewer._search._current_page)[0]
        rect = match.rectangles()[0]
        x, y, width, height = viewer.page_layout().page_rect_to_content(
            viewer._search._current_page,
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height(),
        )
        view = viewer._view
        scroll_x = view.horizontalScrollBar().value()
        scroll_y = view.verticalScrollBar().value()
        assert 0 <= x - scroll_x and x + width - scroll_x <= view.viewport().width()
        assert 0 <= y - scroll_y and y + height - scroll_y <= view.viewport().height()
        viewer.search_next()


def test_search_overlay_covers_the_whole_viewport(qtbot, sample_pdf):
    viewer = PdfViewerWidget()
    qtbot.addWidget(viewer)
    viewer.resize(900, 600)
    viewer.show()
    viewer.load(sample_pdf)
    overlay = viewer.findChild(SearchHighlightOverlay)
    viewport = viewer._view.viewport()

    qtbot.waitUntil(lambda: viewport.height() > 400)
    assert overlay.size() == viewport.size()
    viewer.resize(1100, 800)
    qtbot.waitUntil(lambda: overlay.size() == viewport.size())
    assert overlay.height() > 600


def test_short_query_does_not_search(qtbot, window, sample_pdf):
    results = []
    window._viewer.search_results_changed.connect(
        lambda i, n, s: results.append((i, n, s))
    )
    window.open_path(sample_pdf)

    window._viewer.set_search_query("al")
    qtbot.wait(400)  # longer than the debounce delay
    assert results and results[-1] == (0, 0, False)


def test_sidebar_search_label(qtbot, window, sample_pdf):
    window.open_path(sample_pdf)
    search_edit = window._sidebar.findChild(QLineEdit, "searchEdit")
    result_label = window._sidebar.findChild(QLabel, "searchResultLabel")
    search_edit.setText("alchemy")
    qtbot.waitUntil(lambda: result_label.text() == f"1 of {len(SEARCH_PAGES)}")


def test_search_highlights_are_painted(qtbot, window, sample_pdf):
    results = []
    window._viewer.search_results_changed.connect(
        lambda i, n, s: results.append((i, n, s))
    )
    window.open_path(sample_pdf)
    window._viewer.set_search_query("alchemy")
    qtbot.waitUntil(
        lambda: results and results[-1][1] == len(SEARCH_PAGES) and not results[-1][2]
    )

    overlay = window._viewer.findChild(SearchHighlightOverlay)
    assert overlay.isVisible()
    image = overlay.grab().toImage()
    painted = any(
        image.pixelColor(x, y).alpha() > 0
        for x in range(0, image.width(), 2)
        for y in range(0, image.height(), 2)
    )
    assert painted
