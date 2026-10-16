# Architecture

This document describes the planned layered architecture for PDF Alchemy, and
the reasoning behind it. No implementation exists yet — this is the blueprint
the codebase will follow as features are built.

## Goals

- **Keep PDF logic testable without a UI.** Merge/split/rotate/sign
  operations should be verifiable with plain `pytest`, with no Qt event loop
  required.
- **Keep the UI framework swappable in theory.** PySide6 is the chosen UI
  framework, but business logic should not leak Qt types, so a future port
  (e.g. to a web UI or another toolkit) would only require rewriting the `ui/`
  layer.
- **Keep the PDF engine swappable.** `pypdf` is the default editing library,
  but if a feature needs a capability it lacks (e.g. advanced forms), another
  library can be introduced behind the same `core/` interfaces without
  rewriting the UI.

## Layers

```
┌─────────────────────────────────────────────┐
│  ui/            Qt widgets, windows, dialogs │
│                 (PySide6, signals/slots)     │
└───────────────────────┬───────────────────────┘
                         │ calls into
┌───────────────────────▼───────────────────────┐
│  services/      Cross-cutting application      │
│                 services (printing, file I/O,  │
│                 recent files, settings)         │
└───────────────────────┬───────────────────────┘
                         │ calls into
┌───────────────────────▼───────────────────────┐
│  core/          Qt-free PDF domain logic:       │
│                 document model, page            │
│                 operations, signing, export     │
└─────────────────────────────────────────────────┘
```

### `core/` — Qt-free PDF domain logic

Contains all PDF manipulation logic, with **no imports from `PySide6` or any
UI library**. This is the layer unit tests target directly.

- `document.py` — wraps `pypdf` to open, read, and save PDF documents; the
  in-memory representation the rest of the app works with.
- `operations.py` — page-level operations: rotate, merge/combine, split,
  remove, reorder pages.
- `signing.py` — visual signature stamping (`reportlab` overlay merged onto a
  page) and cryptographic PAdES signing (`pyHanko`).
- `export.py` — render pages to images, extract text.

### `services/` — cross-cutting application services

Thin layer connecting `core/` logic to OS/Qt facilities that aren't pure PDF
logic.

- `print_service.py` — wraps `QPrinter`/`QPrintDialog` for the Windows print
  pipeline.
- `file_service.py` — open/save dialogs, file association handling, path
  utilities.
- `recent_files.py` — tracks recently opened files, persisted between
  sessions.
- `settings.py` — application preferences storage (e.g. theme, default
  export folder).

### `ui/` — Qt widgets and windows

All PySide6-specific code lives here. Widgets call into `services/` and
`core/`, but `core/` and `services/` never import from `ui/`.

- `main_window.py` — top-level window: menu bar, toolbar, docking panels.
  Composes the viewer and sidebar panel side by side in a `QSplitter`.
- `viewer/` — the PDF page viewer package:
  - `viewer_widget.py` — `PdfViewerWidget`, a thin coordinator built on
    `QPdfView` / `QPdfDocument`. Emits `page_position_changed(current_page,
    page_count)` so other widgets (e.g. the sidebar) can react without
    reaching into Qt's PDF internals, and exposes `jump_to_page(page_number)`.
  - `page_layout.py` — `PageLayout`, a Qt-free model of where each page sits
    at the current zoom/viewport. Shared by anything that maps page
    coordinates to the screen (current-page detection, search highlights,
    later signature placement). Unit tested without Qt.
  - `zoom.py` — `ZoomController` (zoom state, Ctrl+wheel) and the floating
    `ZoomControl` widget.
  - `search.py` — `SearchController` (debounced query, match navigation) over
    `QPdfSearchModel`; it emits signals and never scrolls or paints itself.
  - `overlays.py` — `SearchHighlightOverlay`; future page overlays (e.g.
    signature placement) belong here.
  - `empty_state.py` — the "no document" card.
- `sidebar/` — right-hand panel package. `sidebar_panel.py` composes
  self-contained sections: `page_nav_section.py` (current/total page; the
  current-page field is editable and emits `page_jump_requested`) and
  `search_section.py` (find field, "x of y", previous/next). New sidebar
  content such as page thumbnails is added as another section here without
  growing `SidebarPanel`.
- `thumbnail_panel.py` — (planned) page thumbnail list for navigation,
  reordering, and multi-select (used for remove/rotate/split operations) —
  to be built as a section inside `sidebar/`.
- `sign_dialog.py` — dialog for drawing/typing/uploading a signature and
  placing it on a page.
- `theme.py` — design-token constants (`Colors`) and `apply_theme(app)`,
  which loads `resources/styles/dark.qss` and applies it to the whole
  application at startup. See [`docs/DESIGN.md`](DESIGN.md) for the full
  design system.

## Data flow example: "Rotate selected pages"

1. User selects pages in `thumbnail_panel.py` and clicks **Rotate** in
   `main_window.py`.
2. The UI layer calls `core.operations.rotate_pages(document, indices, angle)`.
3. `operations.py` mutates the `pypdf`-backed document model in `core/`.
4. The UI layer asks `viewer/viewer_widget.py` to re-render the affected pages.
5. `file_service.py` is used when the user chooses **Save**.

No Qt types cross into `core/` at any point in this flow — the operation
could be unit tested by constructing a document in memory and asserting the
resulting page rotation values.

## Why this split?

- **Testability:** `core/` has no GUI dependency, so CI can run fast,
  headless unit tests on every PDF operation.
- **Library independence:** PDF libraries (`pypdf`, `pyHanko`, rendering via
  `QtPdf`) are only referenced inside `core/`/`services/` implementations, not
  scattered through UI code — easier to swap or add libraries later.
- **Small, focused modules:** each file in `core/` maps to one feature area
  (rotate/merge/split, signing, export), keeping changes localized.

## Open questions / future decisions

- Whether to introduce an explicit ViewModel layer (MVVM) between `ui/` and
  `core/`/`services/`, or rely on Qt's signal/slot model directly — to be
  decided once the first UI screens are built.
- Whether page thumbnails are cached to disk or regenerated on open, once
  performance on large PDFs is measured.
