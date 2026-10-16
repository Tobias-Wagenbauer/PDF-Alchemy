# High-Zoom Tiled Rendering — Implementation Plan

> Status: **not implemented**. This is a design document to pick up later;
> `MAX_ZOOM` is currently capped at `5.00` (500%) in
> [`zoom.py`](../src/pdfalchemy/ui/viewer/zoom.py) until this plan (or an
> alternative) is built and verified.

## Problem

`QPdfView` (`QPdfView.ZoomMode.Custom`, as used in
[`viewer_widget.py`](../src/pdfalchemy/ui/viewer/viewer_widget.py)) does not
tile pages — it rasterizes the **entire page** as one bitmap sized to the
current zoom factor every time it renders. Bitmap memory therefore grows
with the *square* of the zoom factor. Measured on a single A4 page at 96 DPI:

| Zoom | Full-page bitmap (current `QPdfView` behavior) |
|---|---|
| 100% | 793×1122 px ≈ 3.4 MB |
| 500% (current max) | 3968×5612 px ≈ 85 MB |
| 1000% | 7937×11225 px ≈ 340 MB |
| 2000% | 15874×22450 px ≈ 1.4 GB |
| 5000% | 39685×56125 px ≈ **8.5 GB** |

Raising `MAX_ZOOM` to 5000% without changing how rendering works caused the
app to slow down severely and crash (almost certainly an out-of-memory
condition), which is why the cap was reverted to 500%.

## Goal

Allow zoom well beyond 500% (the original ask was 5000%) without the
memory/CPU cost scaling with zoom, so arbitrarily high zoom stays as cheap as
rendering one viewport-sized image.

## Key enabling Qt API

`QPdfDocument.render(page_index, options)` accepts a
`QPdfDocumentRenderOptions` with two relevant properties:

- `setScaledSize(QSize)` — the conceptual size of the *whole page* in pixels
  at the desired zoom (this can be huge, e.g. 39685×56125 at 5000%).
- `setScaledClipRect(QRect)` — restricts the **returned** `QImage` to just
  this sub-rectangle of the scaled page, in the scaled page's own pixel
  coordinate space.

```python
options = QPdfDocumentRenderOptions()
options.setScaledSize(QSize(39685, 56125))       # full page at 5000% zoom
options.setScaledClipRect(QRect(vx, vy, vw, vh))  # just the visible viewport
image = document.render(page_index, options)      # image is only vw x vh pixels!
```

The cost of a render call depends only on the clip-rect (viewport) size, not
on the zoom level — this is the mechanism that makes unbounded zoom safe.

| Zoom | Tiled approach (viewport-only, e.g. 1280×800) |
|---|---|
| 500% | ≈ 4 MB |
| 1000% | ≈ 4 MB |
| 2000% | ≈ 4 MB |
| 5000% | ≈ 4 MB |

## Chosen approach: Hybrid (keep `QPdfView` below a threshold)

- **Below a threshold** (e.g. zoom ≤ 500%, i.e. today's existing range):
  keep `QPdfView` exactly as it is now. Zero risk to current behavior,
  features, and tests.
- **Above the threshold**: swap in a new custom tiled widget that only
  rasterizes the visible viewport portion of the visible page(s).
- Once this is implemented and verified not to regress memory/CPU at high
  zoom, re-raise `MAX_ZOOM` (e.g. back to `50.00` / 5000%) and extend
  `ZOOM_STEPS` accordingly.

This avoids rewriting the whole viewer (a full replacement of `QPdfView` is
a larger, riskier project — see `docs/` alternatives considered below) while
still removing the actual crash risk for the zoom range that caused it.

### New pieces

- `TILED_RENDER_THRESHOLD` constant next to `MAX_ZOOM` in
  [`zoom.py`](../src/pdfalchemy/ui/viewer/zoom.py) (suggested: `5.0`, i.e.
  the current 500% cap).
- A new `ui/viewer/tiled_view.py` with a `TiledPageView(QWidget)` that:
  - Reuses the existing, Qt-independent
    [`PageLayout`](../src/pdfalchemy/ui/viewer/page_layout.py) for page
    pixel positions/sizes at the current zoom — the same geometry already
    used by `SearchHighlightOverlay`, so no new coordinate math needs to be
    invented.
  - On paint/scroll/resize, finds the pages intersecting the visible
    content rect via `PageLayout.pages_in_range(scroll_top, scroll_bottom)`.
  - For each visible page, computes the page-local `scaledClipRect`: the
    portion of the *scaled* page within the viewport, in the page's own
    pixel space (viewport rect minus `layout.tops[index]` /
    `layout.lefts[index]`).
  - Calls `document.render(page_index, options)` with `scaledSize` derived
    from `PageLayout.scale_x` / `scale_y` and the page's point size, and the
    `scaledClipRect` computed above.
  - Paints the returned `QImage` at the correct on-screen position.
- `PdfViewerWidget` (in
  [`viewer_widget.py`](../src/pdfalchemy/ui/viewer/viewer_widget.py)) decides
  which widget is visible/active based on `zoom > TILED_RENDER_THRESHOLD`,
  mirroring the existing `_on_page_count_changed` pattern that already
  toggles widget visibility.
- Scrollbars, jump-to-page, search highlighting, and page-position tracking
  should keep working unmodified across the switch, since they already
  depend only on `PageLayout`, not on `QPdfView` internals.

## Performance/UX details to get right

1. **Debounce re-render during scroll/resize.** Calling `render()`
   synchronously on every scroll pixel will stutter. Coalesce rapid
   scroll/resize events with a short `QTimer` (e.g. 16–50 ms), similar to the
   existing debounce pattern in
   [`search.py`](../src/pdfalchemy/ui/viewer/search.py).
2. **Background rendering.** `QPdfDocument.render()` is synchronous and can
   take tens of milliseconds for a full viewport of fine detail at extreme
   zoom. Run it off the UI thread (`QThreadPool` + `QRunnable`) and post the
   result back via a signal so scrolling/painting never blocks. **Verify
   `QPdfDocument::render()`'s thread-safety guarantees in the Qt 6.12 docs
   before relying on this** — if it isn't safe to call concurrently with
   other document access, serialize render calls through a single worker
   thread instead.
3. **Tile cache.** A small LRU cache keyed by `(page_index, zoom, clip_rect)`
   avoids re-rendering identical content on repaint-only events (e.g.
   window un-minimizing) or small back-and-forth scrolling.
4. **Placeholder while rendering.** Show the last successfully rendered
   image (even if stale/slightly offset) while a fresh tile is computed,
   instead of a blank rectangle, to avoid flicker.
5. **DPI-aware tiles.** Use `devicePixelRatioF()` so tiles render crisply on
   HiDPI displays without introducing another zoom-multiplier bug.

## Suggested incremental steps

1. Add `TILED_RENDER_THRESHOLD` and the mode-switch plumbing, with the
   tiled path initially rendering synchronously and uncached, to validate
   correctness first (unit tests + manual testing at 1000%+).
2. Add the debounce and a simple LRU tile cache.
3. Move rendering to a background thread pool.
4. Re-raise `MAX_ZOOM` (and extend `ZOOM_STEPS`) only once the above is
   verified not to regress memory/CPU at high zoom — re-run the same
   bitmap-size measurement that uncovered the original issue, this time
   measuring actual process RSS rather than theoretical bitmap size.
5. Add regression tests:
   - Unit-test the page-local clip-rect math as a pure function (no Qt
     dependency), following the existing testing style of
     [`page_layout.py`](../src/pdfalchemy/ui/viewer/page_layout.py).
   - A smoke test that opens a document, sets zoom above the threshold, and
     asserts the tiled path is used (e.g. via a spy/mock on `render()`)
     rather than measuring real memory in CI.

## Open questions / risks to resolve during implementation

- Whether `QPdfView` can simply be told to stop rendering while hidden, or
  whether toggling its visibility is enough to avoid wasted renders when the
  tiled widget takes over (likely yes, since `QPdfView` already gets hidden
  by `_on_page_count_changed` when there's no document — verify it behaves
  the same for a hidden-but-still-has-a-document case).
- Whether `QPdfDocument::render()` is safe to call from a background thread
  (see point 2 above) — confirm before implementing step 3.
- Visual seam/flash when switching between `QPdfView` and the tiled widget
  as zoom crosses the threshold — may need a UX pass (e.g. crossfade), or it
  may be acceptable to just accept a one-frame jump given it's a rare zoom
  transition.
- Interaction between the tiled widget and the existing
  `SearchHighlightOverlay` / page-position tracking at extreme zoom — should
  keep working unmodified since both already depend only on `PageLayout`,
  but must be verified once implemented.

## Alternatives considered

- **Full replacement of `QPdfView`** with a tiled renderer for *all* zoom
  levels: removes the two-code-path complexity of the hybrid approach, but
  is a much larger rewrite and risks regressing the currently-working
  normal-zoom experience for no benefit (`QPdfView` is already fine at
  ≤500%). Worth revisiting if the hybrid approach's two-path complexity
  becomes a maintenance burden.
- **Fixed-size background tile cache with a thread pool from the start**
  (i.e. skip straight to the most robust version): more future-proof for
  huge documents and fast scrolling, but higher upfront effort/risk than
  validating correctness with a simple synchronous version first.
- **Simply lowering `MAX_ZOOM` to a smaller but still-safe fixed value**
  (e.g. 1000%) without any rendering changes: much less effort, but doesn't
  reach the originally requested 5000%, and still wastes memory/CPU
  rendering far more pixels than any viewport can display.
