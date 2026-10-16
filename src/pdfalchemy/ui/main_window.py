"""Main application window: menu bar and the PDF viewer.

Deliberately minimal for now — only the "Open", "Close", and "Exit" actions
needed to view a PDF. Toolbar, thumbnail panel, and editing actions
(rotate/merge/split/sign) will be added once this baseline is reviewed.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QCoreApplication, QSettings, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSplitter

from pdfalchemy.services.file_service import prompt_open_pdf_path
from pdfalchemy.ui.sidebar import DEFAULT_WIDTH as SIDEBAR_DEFAULT_WIDTH
from pdfalchemy.ui.sidebar import SidebarPanel
from pdfalchemy.ui.viewer import PdfViewerWidget

_DEFAULT_TITLE = "PDF Alchemy"
_GEOMETRY_KEY = "mainWindow/geometry"


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(_DEFAULT_TITLE)
        self.resize(900, 1000)

        self._viewer = PdfViewerWidget(self)
        self._sidebar = SidebarPanel(self)
        self._viewer.page_position_changed.connect(self._update_sidebar)
        self._viewer.open_requested.connect(self._handle_open)
        self._viewer.search_results_changed.connect(self._sidebar.update_search_results)
        self._sidebar.page_jump_requested.connect(self._viewer.jump_to_page)
        self._sidebar.search_query_changed.connect(self._viewer.set_search_query)
        self._sidebar.search_next_requested.connect(self._viewer.search_next)
        self._sidebar.search_prev_requested.connect(self._viewer.search_prev)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._viewer)
        splitter.addWidget(self._sidebar)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([900 - SIDEBAR_DEFAULT_WIDTH, SIDEBAR_DEFAULT_WIDTH])
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)

        self._create_actions()
        self._create_menu()
        self._set_document_open(False)
        self._restore_window_geometry()

    def _settings(self) -> QSettings | None:
        # Without an organization name Qt has no place to store settings
        # (e.g. in tests), so persistence is skipped.
        if not QCoreApplication.organizationName():
            return None
        return QSettings()

    def _restore_window_geometry(self) -> None:
        settings = self._settings()
        if settings is None:
            return
        geometry = settings.value(_GEOMETRY_KEY)
        if isinstance(geometry, QByteArray):
            # Qt keeps a restored window on a screen that still exists.
            self.restoreGeometry(geometry)

    def closeEvent(self, event: QCloseEvent) -> None:
        if (settings := self._settings()) is not None:
            settings.setValue(_GEOMETRY_KEY, self.saveGeometry())
        super().closeEvent(event)

    def _create_actions(self) -> None:
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self._handle_open)

        self.close_action = QAction("&Close", self)
        self.close_action.setShortcut(QKeySequence.StandardKey.Close)
        self.close_action.triggered.connect(self._handle_close)

        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        self.find_action = QAction("&Find...", self)
        self.find_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_action.triggered.connect(self._sidebar.focus_search)

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.close_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.find_action)

    def _handle_open(self) -> None:
        file_path = prompt_open_pdf_path(self)
        if file_path:
            self.open_path(file_path)

    def open_path(self, file_path: str) -> None:
        """Load the PDF at ``file_path`` (used by the Open dialog and command line)."""
        error = self._viewer.load(file_path)
        if error != QPdfDocument.Error.None_:
            QMessageBox.warning(
                self,
                "Could not open PDF",
                f"Failed to open:\n{file_path}\n\nReason: {error.name}",
            )
            self._set_document_open(False)
            return

        self.setWindowTitle(f"{_DEFAULT_TITLE} — {file_path}")
        self._set_document_open(True)

    def _handle_close(self) -> None:
        self._viewer.close_document()
        self.setWindowTitle(_DEFAULT_TITLE)
        self._set_document_open(False)

    def _set_document_open(self, document_open: bool) -> None:
        self.close_action.setEnabled(document_open)
        self.find_action.setEnabled(document_open)

    def _update_sidebar(self, current_page: int, page_count: int) -> None:
        if page_count <= 0:
            self._sidebar.clear()
        else:
            self._sidebar.set_page_position(current_page, page_count)
