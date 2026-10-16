# Design System

This document defines the visual language for PDF Alchemy: a modern, dark,
native-feeling Windows desktop UI built around **black/near-black surfaces**
with a **deep purple accent**. It is the single source of truth for colors,
typography, spacing, and component styling — implemented in practice as a
Qt stylesheet (QSS) plus a small Python token module, both described below.

Keep this document and the implementation (`resources/styles/dark.qss`,
`ui/theme.py`) in sync whenever either changes.

## Principles

1. **Dark-first, high contrast.** Black/near-black surfaces with
   near-white text, layered in a small number of flat "elevation" steps
   (no drop shadows — shadows read poorly on dark backgrounds; we use thin
   borders instead).
2. **One accent, used deliberately.** Deep purple is reserved for
   primary actions, selection/focus states, and the current-page
   indicator — not scattered everywhere. Everything else stays
   grayscale.
3. **Flat and minimal.** Subtle rounded corners, thin 1px borders/dividers,
   no gradients or skeuomorphism.
4. **Native where it matters.** Windows file/print dialogs and system
   chrome stay native; only in-app widgets (menus, panels, scrollbars,
   buttons) are themed.
5. **Consistent spacing.** All padding/margins come from the 4px spacing
   scale below — no arbitrary pixel values in new components.

## Color palette

### Surfaces (black & shades)

| Token | Hex | Usage |
|---|---|---|
| `surface.0` | `#121214` | App/window background, main PDF viewer background |
| `surface.1` | `#1A1A1D` | Panels: sidebar, menu bar, toolbar |
| `surface.2` | `#242428` | Hover state on panel rows/menu items |
| `surface.3` | `#2D2D33` | Pressed/selected state, input field backgrounds |
| `border` | `#302F36` | 1px dividers between panels, panel outlines |

### Text

| Token | Hex | Usage |
|---|---|---|
| `text.primary` | `#F2F1F5` | Default text, headings |
| `text.secondary` | `#A4A3AD` | Secondary/supporting text, inactive labels |
| `text.disabled` | `#5A5960` | Disabled menu items/buttons |

### Accent — deep purple

| Token | Hex | Usage |
|---|---|---|
| `accent.default` | `#7C3AED` | Primary buttons, current-page number, active/selected state, focus outline |
| `accent.hover` | `#8B5CF6` | Hover state of accent elements |
| `accent.pressed` | `#6D28D9` | Pressed state of accent elements |
| `accent.muted` | `rgba(124, 58, 237, 0.16)` | Subtle accent-tinted background (e.g. selected row highlight) |

### Semantic (reserved for alerts/validation, used sparingly)

| Token | Hex | Usage |
|---|---|---|
| `status.success` | `#22C55E` | Success confirmations |
| `status.warning` | `#F59E0B` | Warnings (e.g. unsaved changes) |
| `status.danger` | `#EF4444` | Errors (e.g. failed to open a PDF) |
| `status.info` | `#38BDF8` | Informational hints |

All tokens are defined once in [`ui/theme.py`](../src/pdfalchemy/ui/theme.py)
(`Colors` class) and in [`resources/styles/dark.qss`](../src/pdfalchemy/resources/styles/dark.qss).
When a color needs to change, update both.

## Typography

- **Font family:** `"Segoe UI Variable", "Segoe UI", sans-serif` — native
  Windows UI font, no bundled custom font for v1.
- **Scale:**

  | Role | Size | Weight | Usage |
  |---|---|---|---|
  | Heading | 13pt | Semibold (600) | Panel section titles (e.g. "Pages") |
  | Body | 10pt | Regular (400) | Menus, labels, default UI text |
  | Caption | 9pt | Regular (400) | Secondary/muted text |
  | Display | 20pt | Semibold (600) | Large status numbers (e.g. current page) |

## Spacing scale

Base unit: **4px**. Only use multiples of this unit for padding, margins,
and gaps: `4, 8, 12, 16, 24, 32px`.

| Token | Value | Typical usage |
|---|---|---|
| `space.xs` | 4px | Tight gaps between icon and label |
| `space.sm` | 8px | Default padding inside compact controls |
| `space.md` | 16px | Panel content padding |
| `space.lg` | 24px | Section spacing within a panel |
| `space.xl` | 32px | Major layout gaps |

## Shape

| Token | Value | Usage |
|---|---|---|
| `radius.sm` | 4px | Small controls (buttons, inputs) |
| `radius.md` | 6px | Panels, menus, cards |
| `radius.lg` | 10px | Dialogs (reserved for future use) |

Borders are always **1px**, using the `border` token above — no shadows.

## Layout

- **Sidebar panel:** fixed-ish width of **240px** (user-resizable via
  splitter, minimum 180px), `surface.1` background, 1px `border` on its
  left edge separating it from the PDF viewer.
- **Main viewer:** takes remaining horizontal space, `surface.0`
  background.
- **Menu bar:** `surface.1` background, `border` bottom divider.

## Components

- **Menus/menu bar items:** transparent by default, `surface.2` on hover,
  `accent.muted` background with `accent.default` text when checked/active.
- **Scrollbars:** slim (10px), `surface.1` track, `surface.3` thumb,
  `accent.default` thumb on hover — replaces the default Windows scrollbar
  chrome to keep the dark theme consistent.
- **Splitter handle:** 1px `border`-colored hairline; highlights
  `accent.default` on hover.
- **Page indicator (sidebar):** section heading "Pages" in `text.secondary`
  caption style. The current page is an **editable field** (not plain
  text) styled to always read as an input — `surface.2` background and a
  `border`-colored outline are visible by default (not just on hover),
  getting a lighter neutral border on hover and an `accent.default` border
  on focus — shown large in `accent.default`, followed by "of N" in
  `text.secondary`. Committing a value (Enter or focus loss) jumps the
  viewer to the start of that page.
- **Buttons (reserved for future toolbar/dialogs):** primary buttons use
  `accent.default` fill with `text.primary` label, `accent.hover` /
  `accent.pressed` on interaction; secondary buttons are outlined with
  `border` and transparent fill.

## Iconography (reserved for future toolbar work)

- Outline/line-style icons (not filled), 20x20px at default toolbar size.
- Single color, following `text.primary` normally and `accent.default`
  when representing an active/selected tool.

## Implementation

- **`resources/styles/dark.qss`** — the actual Qt stylesheet applying this
  palette to `QMainWindow`, `QMenuBar`, `QMenu`, `QScrollBar`, `QSplitter`,
  panel widgets, etc. Loaded once at startup.
- **`ui/theme.py`** — `Colors` class mirroring the hex values above (for any
  code that needs a color value directly, e.g. custom-painted widgets) and
  `apply_theme(app)`, which reads `dark.qss` and calls
  `app.setStyleSheet(...)`.
- Widgets that need targeted styling set a Qt `objectName` (e.g.
  `sidebarPanel`) so the QSS can target them with an ID selector
  (`#sidebarPanel`) without affecting other widgets of the same class.
