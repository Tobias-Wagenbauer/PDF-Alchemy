"""Centered "no document" card shown instead of the page view."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdfalchemy.paths import APP_ICON_PATH


class EmptyStateView(QWidget):
    """Centered "no document" card with an "Open PDF..." button."""

    open_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("emptyStateView")

        icon_label = QLabel(self)
        icon_label.setPixmap(
            QPixmap(str(APP_ICON_PATH)).scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        heading_label = QLabel("No PDF open", self)
        heading_label.setObjectName("emptyStateHeading")
        heading_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        subtitle_label = QLabel("Open a PDF file to start viewing it.", self)
        subtitle_label.setObjectName("emptyStateSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        open_button = QPushButton("Open PDF...", self)
        open_button.setObjectName("emptyStateOpenButton")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.clicked.connect(self.open_requested)

        card = QFrame(self)
        card.setObjectName("emptyStateCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(8)
        card_layout.addWidget(icon_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(heading_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addSpacing(16)
        card_layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Center the card both horizontally and vertically regardless of
        # the available space, using stretches on all sides.
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        outer_layout.addLayout(row)
        outer_layout.addStretch(1)
