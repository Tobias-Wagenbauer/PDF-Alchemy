"""File open/save dialogs and related path utilities.

Qt dialogs are used here (rather than a lower-level Windows API) because
QFileDialog already renders as the native Windows file picker while staying
cross-platform; this keeps the only Qt-specific "OS integration" concern
isolated to the services layer instead of leaking into ui/ widgets.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QWidget

#: Filter string shown in the native file-open dialog, restricting selection
#: to PDF files (with an "All files" fallback).
PDF_FILE_FILTER = "PDF Files (*.pdf);;All Files (*)"


def prompt_open_pdf_path(parent: QWidget | None = None) -> str | None:
    """Show the native file-open dialog, filtered to PDF files.

    Returns the selected file path, or ``None`` if the user cancelled.
    """
    file_path, _selected_filter = QFileDialog.getOpenFileName(
        parent,
        "Open PDF",
        "",
        PDF_FILE_FILTER,
    )
    return file_path or None
