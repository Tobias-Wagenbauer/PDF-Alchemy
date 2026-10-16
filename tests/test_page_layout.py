"""Unit tests for the Qt-free page geometry model."""

from __future__ import annotations

import pytest

from pdfalchemy.ui.viewer.page_layout import LayoutParams, PageLayout

# 72 dpi at scale 1.0 maps one PDF point to exactly one pixel.
PARAMS = LayoutParams(
    dpi_x=72.0,
    dpi_y=72.0,
    scale=1.0,
    margin_left=6,
    margin_right=6,
    margin_top=6,
    page_spacing=10,
    viewport_width=412,
)
# Three pages: 400x100, 200x100 (narrower), 400x50 (shorter).
SIZES = [(400.0, 100.0), (200.0, 100.0), (400.0, 50.0)]


@pytest.fixture
def layout() -> PageLayout:
    page_layout = PageLayout()
    page_layout.rebuild(SIZES, PARAMS)
    return page_layout


def test_vertical_stacking(layout):
    assert layout.page_count == 3
    assert layout.tops == [6, 116, 226]
    assert layout.bottoms == [106, 216, 276]


def test_pages_are_centred_in_the_content_column(layout):
    # Viewport content width equals the widest page, so it starts at the margin.
    assert layout.lefts == [6.0, 106.0, 6.0]


def test_narrow_content_is_centred_in_a_wide_viewport():
    page_layout = PageLayout()
    wide = LayoutParams(**{**PARAMS.__dict__, "viewport_width": 812})
    page_layout.rebuild(SIZES, wide)
    assert page_layout.lefts == [206.0, 306.0, 206.0]


def test_wide_content_is_left_aligned_against_the_margin():
    page_layout = PageLayout()
    narrow = LayoutParams(**{**PARAMS.__dict__, "viewport_width": 100})
    page_layout.rebuild(SIZES, narrow)
    assert page_layout.lefts == [6.0, 106.0, 6.0]


def test_scale_applies_dpi_and_zoom():
    page_layout = PageLayout()
    params = LayoutParams(
        **{**PARAMS.__dict__, "dpi_x": 144.0, "dpi_y": 144.0, "scale": 0.5}
    )
    page_layout.rebuild(SIZES, params)
    assert page_layout.scale_x == pytest.approx(1.0)
    assert page_layout.scale_y == pytest.approx(1.0)


def test_matches_and_invalidate(layout):
    assert layout.matches(PARAMS)
    assert not layout.matches(LayoutParams(**{**PARAMS.__dict__, "scale": 2.0}))
    layout.invalidate()
    assert not layout.matches(PARAMS)


def test_pages_in_range(layout):
    assert list(layout.pages_in_range(0, 50)) == [0]
    assert list(layout.pages_in_range(100, 120)) == [0, 1]
    assert list(layout.pages_in_range(106, 116)) == []  # only the gap between pages
    assert list(layout.pages_in_range(0, 1000)) == [0, 1, 2]
    assert list(layout.pages_in_range(500, 600)) == []


def test_visible_page_is_the_one_with_most_visible_area(layout):
    # Viewport 100px tall: page 0 is fully visible when scrolled to 6.
    assert layout.visible_page_index(6, 100, 1000) == 0
    # Scrolled so page 0 has 20px visible and page 1 has 70px.
    assert layout.visible_page_index(86, 100, 1000) == 1


def test_visible_page_ties_go_to_the_earliest_page(layout):
    # Page 0 and page 1 both show exactly 45px.
    assert layout.visible_page_index(61, 100, 1000) == 0


def test_scrolled_to_the_bottom_selects_the_last_page(layout):
    assert layout.visible_page_index(1000, 100, 1000) == 2
    # No scrolling possible: fall back to the largest-visible rule.
    assert layout.visible_page_index(0, 400, 0) == 0


def test_page_rect_to_content_maps_points_to_pixels(layout):
    assert layout.page_rect_to_content(1, 10.0, 20.0, 30.0, 5.0) == (
        116.0,
        136.0,
        30.0,
        5.0,
    )


def test_reveal_keeps_scroll_while_rect_is_inside_the_centre_zone(layout):
    # 100x100 viewport: the central 70% spans 15..85 on both axes.
    rect = (20.0, 20.0, 10.0, 10.0)  # content (26, 26)
    assert layout.scroll_to_reveal(0, rect, (0, 0), (100, 100)) == (0, 0)


def test_reveal_centres_rect_outside_the_zone_per_axis(layout):
    # Page 2 starts at y=226, far below the viewport; x=26 is still inside it.
    rect = (20.0, 0.0, 10.0, 10.0)
    assert layout.scroll_to_reveal(2, rect, (0, 0), (100, 100)) == (0, 181)


def test_reveal_rect_in_viewport_but_outside_the_zone_is_recentred(layout):
    # Visible (y=90..100) but in the bottom margin band of the viewport.
    rect = (20.0, 84.0, 10.0, 10.0)
    assert layout.scroll_to_reveal(0, rect, (0, 0), (100, 100)) == (0, 45)


def test_reveal_rect_larger_than_the_zone_is_centred(layout):
    rect = (0.0, 0.0, 400.0, 100.0)  # content (6, 6, 400, 100)
    assert layout.scroll_to_reveal(0, rect, (0, 0), (100, 100)) == (156, 6)


def test_empty_layout_is_safe():
    page_layout = PageLayout()
    page_layout.rebuild([], PARAMS)
    assert page_layout.page_count == 0
    assert page_layout.visible_page_index(0, 100, 0) == 0
    assert list(page_layout.pages_in_range(0, 100)) == []
