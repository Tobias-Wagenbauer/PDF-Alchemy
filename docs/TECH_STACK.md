# Tech Stack

This document records *why* each library was chosen, what alternatives were
considered, and licensing implications — so future contributors understand
the reasoning instead of just the decision.

## Summary

| Concern | Choice | License |
|---|---|---|
| Language | Python 3.11+ (developed & tested on 3.14 via the `pdf_alchemy` conda env) | PSF License |
| UI framework | [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python) | LGPLv3 |
| PDF rendering/viewing | Qt's built-in `QtPdf` module (`QPdfDocument`/`QPdfView`) | LGPLv3 (part of Qt/PySide6) |
| PDF editing (merge/split/rotate/remove) | [`pypdf`](https://pypdf.readthedocs.io/) | MIT |
| Visual signature stamping | [`reportlab`](https://www.reportlab.com/opensource/) | BSD |
| Cryptographic signing (PAdES) | [`pyHanko`](https://github.com/MatthiasValvekens/pyHanko) | MIT |
| Printing | Qt's `QPrinter` / `QPrintDialog` (part of PySide6) | LGPLv3 |
| Packaging | [PyInstaller](https://pyinstaller.org/) | GPLv2 with a linking exception (safe for closed or open-source apps it bundles) |
| Installer | [Inno Setup](https://jrsoftware.org/isinfo.php) | Free for any use (custom license) |
| Testing | `pytest`, `pytest-qt` | MIT |

All runtime libraries are permissive (MIT/BSD) or LGPL, which keeps the
project genuinely free to use, modify, and distribute — including
commercially, if that ever changes — without being forced to open-source
downstream users' code.

## Why PySide6 over PyQt6?

Both are official-quality Qt bindings for Python with near-identical APIs.
PySide6 is maintained directly by The Qt Company and licensed under **LGPLv3**,
meaning it can be used in any application, open or closed source, as long as
Qt itself isn't modified and is dynamically linked (which is the default).
PyQt6 is dual-licensed under **GPLv3 or a paid commercial license** — fine for
an open-source project, but a less flexible default. Since this project may
as well keep its options open, PySide6 was the safer default.

## Why `pypdf` instead of PyMuPDF (`fitz`)?

[PyMuPDF](https://pymupdf.readthedocs.io/) is the most popular and arguably
most powerful PDF library in Python — it handles rendering *and* editing in
one package. However, it is licensed under **AGPLv3** (or a paid commercial
license from Artifex). AGPL requires that any software using it — including
software only used over a network — make its complete source available under
AGPL terms too.

Since this project is open source anyway, PyMuPDF would have been a valid
choice. We chose **`pypdf`** (MIT) instead to:

- Keep licensing simple and unambiguous for all contributors and forks.
- Avoid foreclosing the option of ever distributing a closed-source build or
  a commercial edition later, without having to rip out a core dependency.

`pypdf` does not handle rendering (turning a PDF page into a displayable
image) — that gap is filled by Qt's own `QtPdf` module instead, which is
built on Google's PDFium and ships with PySide6 at no extra licensing cost.

## Why `pyHanko` for cryptographic signing?

Digital, certificate-based PDF signatures (PAdES) are a specialized niche.
`pyHanko` is MIT-licensed, actively maintained, and specifically designed for
PAdES-compliant signing in Python — a good fit without licensing concerns.
Simpler "visual stamp" signatures (drawing/typing a signature image) don't
need this at all — those are just an overlay image merged onto a page via
`reportlab` + `pypdf`.

## Why PyInstaller + Inno Setup for packaging?

- **PyInstaller** bundles the Python interpreter and all dependencies into a
  standalone `.exe`, so end users don't need Python installed.
- **Inno Setup** wraps that output into a proper Windows installer: Start
  Menu shortcuts, `.pdf` file association, an uninstaller entry in "Apps &
  Features", and optional custom install options.

Alternatives considered: `cx_Freeze` (less mature ecosystem/community than
PyInstaller), WiX (more powerful but steeper learning curve than Inno Setup
for a single-app installer), MSIX (nice Windows Store integration, but more
setup overhead for a first release — may be revisited later).

## Alternatives considered for the overall stack

See the project's original planning discussion for the broader comparison
(C#/WPF, Electron, C++/Qt). Python + PySide6 was chosen for the fastest path
to a working personal tool, given the existing Python familiarity on this
project, while still producing a fully native-feeling Windows app via Qt
widgets.
