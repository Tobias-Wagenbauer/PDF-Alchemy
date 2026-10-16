# Features

Detailed breakdown of planned features, their implementation approach, and
status. Update the **Status** column as work progresses.

Status legend: 📋 Planned · 🔨 In progress · ✅ Done

## UI & design system

| Feature | Description | Implementation approach | Status |
|---|---|---|---|
| Dark theme (black + deep purple accent) | App-wide visual theme per the design system | `resources/styles/dark.qss` applied via `ui/theme.apply_theme()`; tokens documented in [`docs/DESIGN.md`](DESIGN.md) | ✅ |

## Core PDF operations

| Feature | Description | Implementation approach | Status |
|---|---|---|---|
| Open & view | Open a PDF (via native file dialog) and render pages for viewing | `QPdfDocument` + `QPdfView`, wired through `services/file_service.py` → `ui/viewer/viewer_widget.py` → `ui/main_window.py` | ✅ (bare minimum: open, view, close) |
| Page position indicator | Right-hand sidebar showing current/total page | `ui/sidebar/page_nav_section.py`, driven by `PdfViewerWidget.page_position_changed` (from `QPdfPageNavigator`/`QPdfDocument`) | ✅ |
| Jump to page | Type a page number in the sidebar and jump the view to its start | Editable `QLineEdit` in `ui/sidebar/page_nav_section.py` emits `page_jump_requested`; `PdfViewerWidget.jump_to_page()` calls `QPdfPageNavigator.jump(page_index, QPointF(0, 0))` | ✅ |
| Page thumbnails | Sidebar list of page previews for navigation | Low-res renders via `QPdfDocument.render()` | 📋 |
| Zoom & pan | Zoom in/out and pan around a page | `QPdfView` in `MultiPage` mode; Ctrl+wheel and a floating `-`/`100%`/`+` control zoom 10%–500% (100% = fit-to-width on load). Panning is via scrolling | ✅ |
| Find in document | Auto-search (debounced, 3+ chars) for text, "x of y" counter, next/prev navigation, all matches highlighted on the page | `QPdfSearchModel` (Qt's built-in async text search) + a custom-painted overlay in `ui/viewer/overlays.py` (state in `ui/viewer/search.py`); search UI lives in `ui/sidebar/search_section.py`; Ctrl+F / Edit → Find... focuses it | ✅ |
| Rotate pages | Rotate one or more selected pages (90/180/270°) | `pypdf` `PageObject.rotate()` | 📋 |
| Combine PDFs | Merge multiple PDF files into one, in chosen order | `pypdf.PdfWriter.append()` per source file | 📋 |
| Remove pages | Delete selected pages from a document | Build new `PdfWriter`, skip removed indices | 📋 |
| Split PDF | Cut a document into multiple PDFs by page ranges | Iterate ranges, write each as a separate `PdfWriter` output | 📋 |
| Reorder pages | Drag-and-drop page reordering in the thumbnail panel | Reorder page list, rebuild `PdfWriter` output | 📋 |

## Signing

| Feature | Description | Implementation approach | Status |
|---|---|---|---|
| Visual signature stamp | Draw, type, or upload a signature image and place it on a page | `reportlab` overlay merged onto the target page via `pypdf` | 📋 |
| Cryptographic signature | Apply a PAdES-compliant digital signature using a certificate | `pyHanko` signing with a PKCS#12/PEM certificate | 📋 |
| Signature placement UI | Drag/resize/position the signature before applying | Custom `sign_dialog.py` widget | 📋 |

## Windows integration

| Feature | Description | Implementation approach | Status |
|---|---|---|---|
| Print | Print the document via the native Windows print dialog | `QPrinter` + `QPrintDialog` | 📋 |
| Save / Save As | Standard save workflow with file dialogs | `pypdf` writer + `QFileDialog` | 📋 |
| Recent files | Quick access to recently opened documents | Persisted list in `services/recent_files.py` | 📋 |
| File associations | "Open with PDF Alchemy" from Windows Explorer | Registered during installer setup (Inno Setup) | 📋 |
| Drag & drop | Drop PDF files onto the app window to open them | Qt drag-and-drop event handling | 📋 |

## Export

| Feature | Description | Implementation approach | Status |
|---|---|---|---|
| Export to images | Save pages as PNG/JPEG | `QPdfDocument.render()` → `QImage.save()` | 📋 |
| Export to text | Extract plain text from a PDF | `pypdf` `page.extract_text()` | 📋 |
| Export to other formats (stretch) | PDF → Word/other formats | No solid free library identified yet; may require an external tool or remain out of scope | 📋 (low priority / under research) |

## Packaging & distribution

| Feature | Description | Implementation approach | Status |
|---|---|---|---|
| Standalone executable | Build a Windows `.exe` | PyInstaller | 📋 |
| Installer | Installer with shortcuts, file association, uninstaller | Inno Setup script in `installer/` | 📋 |

## Non-goals (for now)

- Cloud sync / online storage integration
- Collaborative/multi-user editing
- Mobile or cross-platform builds (Windows-only for v1)
- Full PDF form-filling support (may be revisited later)
