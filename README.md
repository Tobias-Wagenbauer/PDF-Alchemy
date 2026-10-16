# PDF Alchemy

A free, open-source Windows desktop application for viewing and editing PDF
files — sign, rotate, merge, split, remove pages, print, and export, all from
a single native app.

> **Status:** 🚧 Early development. A bare-minimum viewer (open/view/close a
> PDF) is working — see [Roadmap](#roadmap) below.

> **Note on AI-assisted development:** This project was "vibe coded" — written
> largely by an AI assistant, with me ([Tobias Wagenbauer](LICENSE)) directing
> it and reviewing the results. Expect rough edges, and please review the code
> yourself before relying on it for anything important. Bug reports and pull
> requests are welcome.

## Why this project?

Most free PDF tools are either web-based (privacy concerns, upload limits) or
bloated commercial suites. This project aims to be a lightweight, native
Windows app that covers the handful of PDF operations people need most,
without ads, subscriptions, or uploading files to a server.

## Planned features

| Feature | Description |
|---|---|
| **View** | Open and read PDFs with zoom, page navigation, and thumbnails |
| **Sign** | Stamp a drawn/typed/image signature onto a page, or apply a cryptographic (PAdES) digital signature |
| **Rotate pages** | Rotate individual pages or the whole document |
| **Combine PDFs** | Merge multiple PDF files into one |
| **Remove pages** | Delete selected pages from a document |
| **Split PDF** | Cut a document into multiple PDFs by page range |
| **Print** | Print via the native Windows print dialog |
| **Save / Save As** | Standard file save workflow, with autosave recovery |
| **Export** | Export pages to images (PNG/JPEG) or extract text |

See [`docs/FEATURES.md`](docs/FEATURES.md) for the detailed feature breakdown
and status tracking.

## Tech stack

- **Language:** Python 3.11+
- **UI framework:** [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python)
- **PDF rendering:** Qt's built-in `QtPdf` module (`QPdfDocument` / `QPdfView`)
- **PDF editing:** [`pypdf`](https://pypdf.readthedocs.io/) (merge, split, rotate, remove pages)
- **Signing:** [`reportlab`](https://www.reportlab.com/opensource/) (visual stamp overlays) and [`pyHanko`](https://github.com/MatthiasValvekens/pyHanko) (cryptographic PAdES signatures)
- **Printing:** Qt's `QPrinter` / `QPrintDialog`
- **Packaging:** [PyInstaller](https://pyinstaller.org/) + [Inno Setup](https://jrsoftware.org/isinfo.php)

All chosen libraries are MIT/BSD/LGPL-licensed, keeping the project free to
use, modify, and distribute. See [`docs/TECH_STACK.md`](docs/TECH_STACK.md)
for the full rationale, including why libraries like PyMuPDF were
deliberately avoided (AGPL licensing).

## Project structure

```
PDF-Alchemy/
  pyproject.toml          # Project metadata & planned dependencies
  src/pdfalchemy/
    __main__.py           # Application entry point
    app.py                # QApplication setup
    ui/                    # Qt widgets & windows (main window, viewer, dialogs)
    core/                  # Qt-free PDF logic (document, operations, signing, export)
    services/              # Cross-cutting services (printing, files, settings)
    resources/             # Icons & stylesheets
  tests/                   # Unit tests for core/ logic
  installer/               # Inno Setup packaging scripts
  docs/                    # Architecture & planning documentation
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a full explanation of
how the layers fit together and why.

## Getting started

```powershell
conda activate pdf_alchemy
pip install -r requirements.txt   # reproduce the exact pinned environment
pip install -e .                  # install the pdfalchemy package itself
python -m pdfalchemy               # launch the app
```

This currently gets you a bare-minimum window: **File → Open** (native
Windows file picker, filtered to `*.pdf`), a scrollable page view, and
**File → Close**. See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for full
environment details and [`docs/FEATURES.md`](docs/FEATURES.md) for what's
implemented vs. still planned.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layered architecture, data flow, design decisions
- [`docs/DESIGN.md`](docs/DESIGN.md) — visual design system: colors, typography, spacing, components
- [`docs/FEATURES.md`](docs/FEATURES.md) — detailed feature list & implementation status
- [`docs/TECH_STACK.md`](docs/TECH_STACK.md) — libraries used, alternatives considered, licensing notes
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — planned setup, run, test, and packaging workflow
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — notable changes over time
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute

## Roadmap

1. Scaffold project structure & documentation ✅
2. Set up development environment (conda `pdf_alchemy`, dependencies installed) ✅
3. Basic PDF viewer: open file via native dialog, render pages, close ✅
4. Design system (dark theme, deep purple accent) + page position sidebar, jump to page, zoom, find in document ✅
5. Core page operations (rotate, merge, split, remove pages) 🔨 (next step)
6. Printing & save/export
7. Signature stamping (visual overlay)
8. Cryptographic signing (PAdES)
9. Packaging (PyInstaller + Inno Setup installer, incl. `.pdf` file association) ✅ (unsigned for now)
10. Polish: recent files, settings, drag & drop, thumbnails
11. Code-sign the executable and installer (code-signing certificate, `signtool` / Inno Setup `SignTool`) so Windows SmartScreen and UAC show a verified publisher for public distribution

## License

This project is licensed under the [MIT License](LICENSE).
