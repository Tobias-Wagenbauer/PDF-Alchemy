"""Zoom state, the Ctrl+wheel handler, and the floating zoom control widget."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPointF, Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QWidget

MIN_ZOOM = 0.10
MAX_ZOOM = 50.00
#: Fixed levels used by the +/- buttons.
ZOOM_STEPS = (
    0.10,
    0.25,
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
    2.00,
    3.00,
    4.00,
    5.00,
    10.00,
    20.00,
    30.00,
    40.00,
    50.00,
)
#: Zoom multiplier per mouse-wheel notch (120 angle-delta units).
_WHEEL_ZOOM_BASE = 1.1
_WHEEL_NOTCH = 120
_POINTS_PER_INCH = 72.0


class ZoomControl(QFrame):
    """Floating ``[-] 100% [+]`` control; the percentage button resets to 100%."""

    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("zoomControl")

        self._out_button = QPushButton("\u2212", self)
        self._out_button.setObjectName("zoomOutButton")
        self._out_button.setToolTip("Zoom out")
        self._out_button.clicked.connect(self.zoom_out_requested)

        self._value_button = QPushButton("100%", self)
        self._value_button.setObjectName("zoomValueButton")
        self._value_button.setToolTip("Reset to 100%")
        self._value_button.setMinimumWidth(56)
        self._value_button.clicked.connect(self.reset_requested)

        self._in_button = QPushButton("+", self)
        self._in_button.setObjectName("zoomInButton")
        self._in_button.setToolTip("Zoom in")
        self._in_button.clicked.connect(self.zoom_in_requested)

        for button in (self._out_button, self._value_button, self._in_button):
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addWidget(self._out_button)
        layout.addWidget(self._value_button)
        layout.addWidget(self._in_button)

    def set_zoom(self, zoom_factor: float) -> None:
        """Update the displayed percentage and the buttons' enabled state."""
        self._value_button.setText(f"{round(zoom_factor * 100)}%")
        self._out_button.setEnabled(zoom_factor > MIN_ZOOM + 1e-6)
        self._in_button.setEnabled(zoom_factor < MAX_ZOOM - 1e-6)


class ZoomController(QObject):
    """Owns the zoom factor of a ``QPdfView`` and applies it to the view.

    The user-facing zoom is relative to a "fit to width" base scale computed
    when a document loads, so 100% matches how the document first appears.
    Also installs a Ctrl+wheel zoom handler on the view's viewport.
    """

    #: Emitted after the zoom factor changed (1.0 == 100%).
    zoom_changed = Signal(float)

    def __init__(
        self, view: QPdfView, document: QPdfDocument, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._document = document
        self._zoom = 1.0
        self._base_scale = 1.0
        self._wheel_remainder = 0
        self._viewport = view.viewport()
        self._viewport.installEventFilter(self)

    @property
    def zoom(self) -> float:
        """Current zoom factor (1.0 == 100%)."""
        return self._zoom

    @property
    def base_scale(self) -> float:
        """Scale at which 100% zoom fits the widest page to the viewport width."""
        return self._base_scale

    @property
    def total_scale(self) -> float:
        """Zoom factor relative to Qt's 1:1 rendering."""
        return self._zoom * self._base_scale

    def set_zoom_factor(self, factor: float, anchor: QPointF | None = None) -> None:
        """Zoom to ``factor`` (clamped), keeping the viewport point ``anchor`` fixed.

        ``anchor`` defaults to the centre of the viewport.
        """
        factor = max(MIN_ZOOM, min(MAX_ZOOM, factor))
        if abs(factor - self._zoom) < 1e-9:
            return

        viewport = self._view.viewport()
        if anchor is None:
            anchor = QPointF(viewport.width() / 2, viewport.height() / 2)
        h_bar = self._view.horizontalScrollBar()
        v_bar = self._view.verticalScrollBar()
        ratio = factor / self._zoom
        new_h = (h_bar.value() + anchor.x()) * ratio - anchor.x()
        new_v = (v_bar.value() + anchor.y()) * ratio - anchor.y()

        self._zoom = factor
        self._view.setZoomFactor(self.total_scale)
        # The scroll ranges are updated synchronously by setZoomFactor().
        h_bar.setValue(round(new_h))
        v_bar.setValue(round(new_v))

        self.zoom_changed.emit(factor)

    def zoom_in(self) -> None:
        """Zoom to the next fixed step above the current zoom."""
        for step in ZOOM_STEPS:
            if step > self._zoom + 0.005:
                self.set_zoom_factor(step)
                return

    def zoom_out(self) -> None:
        """Zoom to the next fixed step below the current zoom."""
        for step in reversed(ZOOM_STEPS):
            if step < self._zoom - 0.005:
                self.set_zoom_factor(step)
                return

    def reset_zoom(self) -> None:
        """Return to 100%."""
        self.set_zoom_factor(1.0)

    def fit_to_width(self) -> None:
        """Make the loaded document fit the viewport width and reset to 100%."""
        margins = self._view.documentMargins()
        available = (
            self._view.viewport().width()
            - self._view.verticalScrollBar().sizeHint().width()
            - margins.left()
            - margins.right()
        )
        widest = max(
            (
                self._document.pagePointSize(index).width()
                for index in range(self._document.pageCount())
            ),
            default=0.0,
        )
        # Qt's zoom factor 1.0 renders a point as logicalDpi/72 pixels.
        full_width = widest * self._view.logicalDpiX() / _POINTS_PER_INCH
        self._base_scale = (
            available / full_width if full_width > 0 and available > 0 else 1.0
        )

        self._zoom = 1.0
        self._wheel_remainder = 0
        self._view.setZoomFactor(self._base_scale)
        self.zoom_changed.emit(self._zoom)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            watched is self._viewport
            and event.type() == QEvent.Type.Wheel
            and isinstance(event, QWheelEvent)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._handle_ctrl_wheel(event)
            return True
        return super().eventFilter(watched, event)

    def _handle_ctrl_wheel(self, event: QWheelEvent) -> None:
        if self._document.pageCount() > 0:
            # Accumulate so smooth-scrolling devices (touchpads) zoom fluidly.
            self._wheel_remainder += event.angleDelta().y()
            notches = self._wheel_remainder / _WHEEL_NOTCH
            if notches:
                self._wheel_remainder = 0
                self.set_zoom_factor(
                    self._zoom * _WHEEL_ZOOM_BASE**notches, event.position()
                )
        event.accept()
