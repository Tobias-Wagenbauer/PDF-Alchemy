"""Pure page-geometry model of a vertical multi-page view.

Mirrors how ``QPdfView`` (``MultiPage`` mode) stacks pages, but has no Qt
dependency: it only turns page sizes (in PDF points) plus a few view
parameters into pixel positions. That makes the maths unit-testable and
reusable by anything that needs to map page coordinates to the scrolled
viewport (search highlights today; signature placement later).
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from dataclasses import dataclass

POINTS_PER_INCH = 72.0
#: Share of the viewport (per axis, around its centre) in which a target
#: counts as comfortably visible and the view is left where it is.
CENTER_ZONE_FRACTION = 0.7


@dataclass(frozen=True)
class LayoutParams:
    """Everything besides the page sizes that influences the layout."""

    dpi_x: float
    dpi_y: float
    #: Total zoom applied on top of Qt's 1:1 rendering (user zoom x fit-to-width base).
    scale: float
    margin_left: int
    margin_right: int
    margin_top: int
    page_spacing: int
    viewport_width: int


def _scroll_axis_to_reveal(
    start: float, size: float, scroll: int, viewport: int, zone: float
) -> int:
    """Scroll offset along one axis that brings ``[start, start + size]`` into view.

    Returns ``scroll`` unchanged while the range lies inside the central
    ``zone`` of the viewport, otherwise the offset that centres it.
    """
    margin = viewport * (1 - zone) / 2
    if start >= scroll + margin and start + size <= scroll + viewport - margin:
        return scroll
    return round(start + size / 2 - viewport / 2)


class PageLayout:
    """Pixel positions of every page in the scrolled content area.

    Rebuilt lazily by the owner: call :meth:`matches` with the current
    :class:`LayoutParams` and :meth:`rebuild` when it returns ``False``;
    call :meth:`invalidate` when the page sizes themselves change.
    """

    def __init__(self) -> None:
        self._params: LayoutParams | None = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.tops: list[int] = []
        self.bottoms: list[int] = []
        self.lefts: list[float] = []

    @property
    def page_count(self) -> int:
        return len(self.tops)

    def invalidate(self) -> None:
        """Force the next :meth:`matches` call to report a stale layout."""
        self._params = None

    def matches(self, params: LayoutParams) -> bool:
        """Whether the layout is already up to date for ``params``."""
        return self._params == params

    def rebuild(
        self, page_sizes: Sequence[tuple[float, float]], params: LayoutParams
    ) -> None:
        """Recompute all page positions from ``page_sizes`` (points) and ``params``."""
        self._params = params
        self.scale_x = params.dpi_x / POINTS_PER_INCH * params.scale
        self.scale_y = params.dpi_y / POINTS_PER_INCH * params.scale

        # Each page is centred horizontally within a shared content column as
        # wide as the widest page. That column is itself centred in the
        # viewport, or left-aligned against the margin once it is wider than
        # the viewport (scrolling horizontally from there).
        widths = [width * self.scale_x for width, _height in page_sizes]
        content_width = max(widths, default=0.0)
        available_width = (
            params.viewport_width - params.margin_left - params.margin_right
        )
        content_left = params.margin_left + max(
            0.0, (available_width - content_width) / 2
        )

        self.tops = []
        self.bottoms = []
        self.lefts = []
        y = params.margin_top
        for (_width, height_points), width in zip(page_sizes, widths):
            height = round(height_points * self.scale_y)
            self.tops.append(y)
            self.bottoms.append(y + height)
            self.lefts.append(content_left + (content_width - width) / 2)
            y += height + params.page_spacing

    def first_page_ending_after(self, y: float) -> int:
        """Index of the first page whose bottom edge lies below ``y``."""
        return bisect_right(self.bottoms, y)

    def pages_in_range(self, top: float, bottom: float) -> range:
        """Indices of the pages intersecting the content range ``[top, bottom)``."""
        first = self.first_page_ending_after(top)
        end = bisect_left(self.tops, bottom, lo=first)
        return range(first, end)

    def visible_page_index(
        self, scroll_top: int, viewport_height: int, max_scroll: int
    ) -> int:
        """Index of the page with the largest visible area (earliest on ties).

        The last page wins once the view is scrolled all the way down, since
        a short final page may never become the largest visible one.
        """
        last = len(self.tops) - 1
        if last < 0:
            return 0
        if max_scroll > 0 and scroll_top >= max_scroll:
            return last

        bottom = scroll_top + viewport_height
        best_index = min(self.first_page_ending_after(scroll_top), last)
        best_visible = -1
        for index in self.pages_in_range(scroll_top, bottom):
            visible = min(bottom, self.bottoms[index]) - max(
                scroll_top, self.tops[index]
            )
            if visible > best_visible:
                best_index, best_visible = index, visible
        return best_index

    def scroll_to_reveal(
        self,
        page_index: int,
        rect: tuple[float, float, float, float],
        scroll: tuple[int, int],
        viewport: tuple[int, int],
        zone: float = CENTER_ZONE_FRACTION,
    ) -> tuple[int, int]:
        """New ``(scroll_x, scroll_y)`` that keeps ``rect`` comfortably in view.

        ``rect`` is ``(x, y, width, height)`` in page points. Each axis is
        only changed when the rectangle lies outside the central ``zone``
        (a fraction of the viewport) on that axis, in which case it is
        centred. The result is not clamped to the scrollable range.
        """
        x, y, width, height = self.page_rect_to_content(page_index, *rect)
        scroll_x, scroll_y = scroll
        viewport_width, viewport_height = viewport
        return (
            _scroll_axis_to_reveal(x, width, scroll_x, viewport_width, zone),
            _scroll_axis_to_reveal(y, height, scroll_y, viewport_height, zone),
        )

    def page_rect_to_content(
        self, page_index: int, x: float, y: float, width: float, height: float
    ) -> tuple[float, float, float, float]:
        """Map a rectangle in page points to content (unscrolled) pixel coordinates."""
        return (
            self.lefts[page_index] + x * self.scale_x,
            self.tops[page_index] + y * self.scale_y,
            width * self.scale_x,
            height * self.scale_y,
        )
