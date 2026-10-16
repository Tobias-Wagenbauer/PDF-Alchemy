# PyInstaller spec for PDF Alchemy. Build from the repo root:
#   pyinstaller pdfalchemy.spec
# ruff: noqa
from pathlib import Path

root = Path(SPECPATH)
icons = root / "src" / "pdfalchemy" / "resources" / "icons"
styles = root / "src" / "pdfalchemy" / "resources" / "styles"

a = Analysis(
    [str(root / "src" / "pdfalchemy" / "__main__.py")],
    pathex=[str(root / "src")],
    datas=[
        (str(icons), "pdfalchemy/resources/icons"),
        (str(styles), "pdfalchemy/resources/styles"),
    ],
    # Qt modules the app never imports; keeps them out of the bundle.
    excludes=[
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtSvg",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "tkinter",
    ],
)
# Drop Qt's UI translation files (the app UI is English only).
a.datas = [d for d in a.datas if "PySide6\\translations" not in d[0].replace("/", "\\")]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PDFAlchemy",
    console=False,
    icon=str(icons / "app.ico"),  # icon embedded in the .exe (Explorer, shortcuts)
)
coll = COLLECT(exe, a.binaries, a.datas, name="PDFAlchemy")
