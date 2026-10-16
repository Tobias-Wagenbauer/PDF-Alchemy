"""Generate the app icon assets from the master ``assets/branding/icon.png``.

Outputs (in ``src/pdfalchemy/resources/icons/``):
- ``app.png`` — 256x256 PNG used by the Qt window/taskbar icon
- ``app.ico`` — multi-size Windows icon (used for the .exe, installer, shortcuts)

Run from the repo root with the project environment:

    python scripts/build_icons.py              # stretch the logo to a square
    python scripts/build_icons.py --no-stretch # keep proportions, center on a square
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "branding" / "icon.png"
OUT_DIR = ROOT / "src" / "pdfalchemy" / "resources" / "icons"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
ALPHA_THRESHOLD = 8  # ignore near-invisible pixels when measuring content
PADDING_RATIO = 0.01  # transparent margin kept around the content, per side


def _fit_to_square(image: QImage, stretch: bool = True) -> QImage:
    """Crop transparent borders, then fit the content onto a square canvas.

    Windows renders the whole canvas, so any transparent padding in the source
    makes the icon look smaller than other apps' icons. With ``stretch`` the
    content is scaled non-uniformly to fill the square; otherwise it is centered.
    """
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = image.width(), image.height()
    left, top, right, bottom = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            if (image.pixel(x, y) >> 24) > ALPHA_THRESHOLD:
                left, right = min(left, x), max(right, x)
                top, bottom = min(top, y), max(bottom, y)
    if right < 0:
        return image
    content = image.copy(left, top, right - left + 1, bottom - top + 1)
    margin = round(max(content.width(), content.height()) * PADDING_RATIO)
    side = max(content.width(), content.height()) + margin * 2
    canvas = QImage(side, side, QImage.Format.Format_ARGB32)
    canvas.fill(Qt.GlobalColor.transparent)
    if stretch:
        content = content.scaled(
            side - margin * 2,
            side - margin * 2,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    painter = QPainter(canvas)
    painter.drawImage(
        (side - content.width()) // 2, (side - content.height()) // 2, content
    )
    painter.end()
    return canvas


def _scaled(image: QImage, size: int) -> QImage:
    return image.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data.data())


def _write_ico(path: Path, image: QImage) -> None:
    """Write a multi-size ICO whose entries are PNG-compressed (Vista+)."""
    frames = [(size, _png_bytes(_scaled(image, size))) for size in ICO_SIZES]
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = len(header) + 16 * len(frames)
    entries = b""
    body = b""
    for size, png in frames:
        dim = 0 if size >= 256 else size  # 0 means 256 in the ICO format
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        body += png
        offset += len(png)
    path.write_bytes(header + entries + body)


def main() -> int:
    _app = QGuiApplication(sys.argv)  # keeps Qt image plugins loaded
    image = QImage(str(SOURCE))
    if image.isNull():
        print(f"Could not read {SOURCE}", file=sys.stderr)
        return 1
    image = _fit_to_square(image, stretch="--no-stretch" not in sys.argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _scaled(image, 256).save(str(OUT_DIR / "app.png"), "PNG")
    _write_ico(OUT_DIR / "app.ico", image)
    print(f"Wrote {OUT_DIR / 'app.png'} and {OUT_DIR / 'app.ico'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
