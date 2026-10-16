# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project intends to follow [Semantic Versioning](https://semver.org/)
once a first release is published.

## [Unreleased]

### Added

- Initial project scaffolding: folder structure, documentation
  (`README.md`, `docs/ARCHITECTURE.md`, `docs/FEATURES.md`,
  `docs/TECH_STACK.md`, `docs/DEVELOPMENT.md`), `pyproject.toml`,
  `.gitignore`, and MIT `LICENSE`.
- Development environment: conda environment `pdf_alchemy` (Python 3.14)
  created, with runtime dependencies (`PySide6`, `pypdf`, `reportlab`,
  `pyhanko`) and dev dependencies (`pytest`, `pytest-qt`, `pyinstaller`,
  `black`, `ruff`) installed and smoke-tested, including `PySide6`'s
  `QtPdf`/`QtPdfWidgets` modules.
- `requirements.txt` — pinned snapshot of the full environment via
  `pip freeze`, for reproducible setup.
- Bare-minimum PDF viewer: open a PDF via the native Windows file dialog,
  view it (scrollable, fit-to-width rendering via `QPdfView`/`QPdfDocument`),
  and close it. Implemented across the planned architecture layers:
  - `services/file_service.py` — native open-file dialog, filtered to PDFs
  - `ui/viewer_widget.py` — `PdfViewerWidget` wrapping `QPdfView`/`QPdfDocument`
  - `ui/main_window.py` — `MainWindow` with File → Open/Close/Exit menu
  - `app.py` / `__main__.py` — `QApplication` bootstrap, runnable via
    `python -m pdfalchemy`
  - Package installed in editable mode (`pip install -e .`) in `pdf_alchemy`
- Design system: [`docs/DESIGN.md`](DESIGN.md) defines the visual language
  (dark/black surfaces, deep purple accent, typography, spacing, shape,
  component rules), implemented as:
  - `resources/styles/dark.qss` — the Qt stylesheet applying the palette to
    the menu bar, menus, sidebar, splitter, scrollbars, buttons, tooltips
  - `ui/theme.py` — `Colors` token constants and `apply_theme(app)`, called
    once at startup from `app.py`
- Page position sidebar: a right-hand panel (`ui/sidebar_panel.py`,
  `SidebarPanel`) showing the current/total page, placed next to the PDF
  viewer in a `QSplitter` (`ui/main_window.py`). `PdfViewerWidget` now emits
  `page_position_changed(current_page, page_count)`, sourced from
  `QPdfDocument.pageCountChanged` and `QPdfPageNavigator.currentPageChanged`,
  so the sidebar stays in sync without `ui/main_window.py` touching Qt's PDF
  internals directly.
- Editable current-page field: the sidebar's current-page display is now a
  `QLineEdit` (`ui/sidebar_panel.py`). Committing an edit (Enter or focus
  loss) clamps the typed value to the valid page range and emits
  `page_jump_requested(page_number)`, which `ui/main_window.py` connects to
  `PdfViewerWidget.jump_to_page()` — using
  `QPdfPageNavigator.jump(page_index, QPointF(0, 0))` to scroll to the start
  (top-left) of that page. In-progress typing is preserved even if a
  scroll-driven update arrives while the field has focus.
- Zoom: Ctrl (Strg) + mouse wheel zooms around the cursor, and a floating
  control at the top-right of the viewer (`ZoomControl` in
  `ui/viewer_widget.py`) shows the current zoom (100% = fit-to-width on
  load), updates live while zooming, steps through fixed levels with its
  `+`/`-` buttons (10%–5000%), and resets to 100% when the percentage is
  clicked.
- Empty-state card: when no document is open (on startup and after
  File → Close), the viewer now shows a centered card (`EmptyStateView` in
  `ui/viewer_widget.py`) with the app icon, a "No PDF open" heading, and an
  "Open PDF..." button (wired to `PdfViewerWidget.open_requested`, which
  `ui/main_window.py` connects to the same handler as File → Open), instead
  of the previous blank scroll area.
- Find in document: a "Search" field in the sidebar (`ui/sidebar_panel.py`)
  auto-searches (debounced, 3-character minimum) using Qt's built-in
  `QPdfSearchModel`, which extracts and matches text off the UI thread so
  results stream in live even on large PDFs. `PdfViewerWidget` jumps to the
  first match as soon as any are found, shows "x of y" (with "..." while
  still searching) via `search_results_changed`, and highlights every match
  on the visible pages with a custom-painted overlay
  (`SearchHighlightOverlay`) — all matches in amber, the current one in the
  accent purple — since `QPdfView` only highlights a single match natively.
  Next/previous (wrapping) via the sidebar's ▲/▼ buttons or Enter/Shift+Enter
  in the field; Ctrl+F (Edit → Find...) focuses the field; closing or
  reloading the document clears the search.

### Changed

- The page indicator no longer relies on `QPdfPageNavigator.currentPage()`,
  which is inaccurate when several pages are visible (zoomed out).
  `PdfViewerWidget` now derives the current page from the scroll position
  (page with the largest visible area; last page at the bottom) and reports
  the requested page right after a sidebar jump.

- The current-page field's "it's an input" affordance (background tint +
  border) is now always visible, not just on hover — the previous
  transparent/invisible default made it easy to miss that the number was
  editable. Hover and focus states remain as progressively stronger
  highlights on top of that base styling.

- UI code structure: the monolithic `ui/viewer_widget.py` and
  `ui/sidebar_panel.py` were split into packages, with no behaviour change.
  `ui/viewer/` now holds `viewer_widget.py` (thin coordinator), `zoom.py`
  (`ZoomController` + `ZoomControl`), `search.py` (`SearchController`),
  `overlays.py` (`SearchHighlightOverlay`), `empty_state.py`, and
  `page_layout.py` (`PageLayout`, a Qt-free page-geometry model that is
  rebuilt automatically when zoom/viewport change). `ui/sidebar/` holds
  `sidebar_panel.py` plus `page_nav_section.py` and `search_section.py`.

### Tests

- Added `tests/test_page_layout.py` (pure unit tests for `PageLayout`) and
  `tests/test_viewer_smoke.py` (headless `pytest-qt` test of open, jump, zoom,
  search, and highlight painting through `MainWindow`).

### Fixed

- Closing a document used to leave the last-viewed page and its scrollbar
  stuck on screen: `QPdfView` doesn't recompute its scroll range on its own
  when the document closes. `PdfViewerWidget` now forces a re-layout (by
  toggling the view's zoom mode) whenever the page count drops to zero, and
  hides the scroll area entirely in favor of the empty-state card.

