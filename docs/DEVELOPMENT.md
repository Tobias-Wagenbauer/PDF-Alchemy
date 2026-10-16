# Development Guide

This describes the developer workflow. The environment and dependencies
below are set up and verified; application code itself hasn't been written
yet (see [Roadmap](../README.md#roadmap)) — the run/test commands will start
producing real output once the first implementation lands.

## Prerequisites

- **Conda** (Anaconda or Miniconda) — used to manage the project's Python
  environment
- **Windows 10/11** (primary target platform; development can still happen
  on other OSes since PySide6/pypdf are cross-platform, but printing and
  packaging steps are Windows-specific)
- **Git**

## Environment: `pdf_alchemy` (conda, Python 3.14)

This project uses a dedicated conda environment named **`pdf_alchemy`**,
running **Python 3.14**. All runtime and dev dependencies (see
[`docs/TECH_STACK.md`](TECH_STACK.md)) have been installed and smoke-tested
into this environment, including confirming that `PySide6` (and its `QtPdf`/
`QtPdfWidgets` modules), `pypdf`, `reportlab`, and `pyhanko` all import
cleanly on Python 3.14.

`pyproject.toml` declares `requires-python = ">=3.14"`: Python 3.14 (via the
`pdf_alchemy` conda environment) is the version the project is developed,
tested, and packaged with.

### Creating the environment (already done, for reference)

```powershell
conda create -n pdf_alchemy python=3.14
```

### Activating the environment

Always activate `pdf_alchemy` before running, testing, or installing anything
for this project:

```powershell
conda activate pdf_alchemy
```

### Installing dependencies

To reproduce the exact environment on another machine, install from the
pinned [`requirements.txt`](../requirements.txt) (generated via `pip freeze`
from `pdf_alchemy`):

```powershell
conda activate pdf_alchemy
pip install -r requirements.txt
```

Alternatively, install the project itself in editable mode, which pulls in
the human-curated dependency list from `pyproject.toml` (looser version
bounds than the exact pins in `requirements.txt`):

```powershell
conda activate pdf_alchemy
pip install -e ".[dev]"
```

### Updating `requirements.txt`

Whenever a dependency is added, removed, or upgraded in the `pdf_alchemy`
environment, regenerate the pinned snapshot so it stays reproducible:

```powershell
conda activate pdf_alchemy
pip freeze > requirements.txt
```

### Installed dependencies (current snapshot)

| Package | Version | Purpose |
|---|---|---|
| PySide6 | 6.12.0 | UI framework + `QtPdf` rendering |
| pypdf | 6.20.1 | PDF merge/split/rotate/remove |
| reportlab | 5.0.1 | Signature stamp overlays |
| pyhanko | 0.37.0 | Cryptographic (PAdES) signing |
| pytest | 9.1.1 | Testing |
| pytest-qt | 4.5.0 | Qt widget testing |
| pyinstaller | 6.22.3 | Standalone `.exe` packaging |
| black | 26.10.1 | Code formatting |
| ruff | 0.17.1 | Linting |

Full transitive dependency list: [`requirements.txt`](../requirements.txt).

## Running the app

The project must be installed in editable mode first so the `pdfalchemy`
package is importable (one-time step, already done in `pdf_alchemy`):

```powershell
conda activate pdf_alchemy
pip install -e .
```

Then run it:

```powershell
conda activate pdf_alchemy
python -m pdfalchemy
```

This currently opens a bare-minimum main window with **File → Open**,
**Close**, and **Exit**. Open prompts the native Windows file picker filtered
to `*.pdf`; the selected file renders in a scrollable, fit-to-width page
view; Close clears the view.

## Planned test workflow

```powershell
conda activate pdf_alchemy
pytest tests/
```

Unit tests should target `core/` logic directly (no UI dependency). UI
interaction tests use `pytest-qt` and run headless (`tests/conftest.py` sets
`QT_QPA_PLATFORM=offscreen`): `tests/test_viewer_smoke.py` drives the viewer
and sidebar through `MainWindow` with a generated PDF, and
`tests/test_page_layout.py` covers the Qt-free page geometry.

## Packaging workflow

See [`RELEASING.md`](RELEASING.md) for the step-by-step guide to building a
new `PDFAlchemy-Setup-<version>.exe` installer (PyInstaller + Inno Setup).

## Coding conventions (planned)

- Follow [PEP 8](https://peps.python.org/pep-0008/); format with `black` and
  lint with `ruff` once added to `dev` dependencies.
- Keep `core/` and `services/` free of `PySide6` imports — see
  [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for why.
- Write unit tests alongside new `core/` modules (`tests/test_<module>.py`).
- Prefer small, focused commits/PRs per feature (e.g. "Add page rotation
  operation", not one giant PR per roadmap phase).

## Branching & commits

- `main` — always kept in a working state.
- Feature branches: `feature/<short-description>` (e.g. `feature/rotate-pages`).
- Commit messages: short imperative summary line, with a brief body if the
  change needs explanation.

This file will be expanded with verified, exact steps as soon as the first
`pyproject.toml` dependencies are pinned and the app actually runs.
