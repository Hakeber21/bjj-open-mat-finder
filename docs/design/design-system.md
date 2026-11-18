# BJJ Open Mat Finder — Design System

Version 1. Owner: designer agent. Builder approves before engineer builds.

---

## 1. Color tokens

| Token                | Hex       | Usage                                              |
|----------------------|-----------|----------------------------------------------------|
| `--color-bg`         | `#12151a` | App background                                     |
| `--color-surface`    | `#1c2028` | Cards, panels, drawers                             |
| `--color-surface-2`  | `#252a34` | Input fields, hover states, nested surfaces        |
| `--color-border`     | `#2e3440` | All dividers and borders                           |
| `--color-text`       | `#e8eaf0` | Primary body text                                  |
| `--color-text-muted` | `#7f8898` | Labels, secondary info, placeholders               |
| `--color-accent`     | `#d95f28` | CTAs, links, active states, FAB (burnt orange)     |
| `--color-accent-dim` | `#7a3415` | Active chip background                             |

### Freshness signal palette (semantic, do not repurpose)

| Token              | Hex       | Meaning                        | Used when                     |
|--------------------|-----------|--------------------------------|-------------------------------|
| `--color-fresh`    | `#22c55e` | Verified < 30 days ago         | Badge, drawer block, marker   |
| `--color-warn`     | `#f59e0b` | 30–90 days ago                 | Badge, drawer block, marker   |
| `--color-stale`    | `#ef4444` | > 90 days ago                  | Badge, drawer block, marker   |

### Format badge palette (semantic, do not repurpose)

| Token             | Hex       | Usage         |
|-------------------|-----------|---------------|
| `--color-gi`      | `#3b82f6` | Gi badge text |
| `--color-nogi`    | `#a855f7` | No-Gi badge   |
| `--color-both`    | `#06b6d4` | Both badge    |

---

## 2. Typography

All type uses the system font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`. No external font load. No paid typefaces.

| Use              | Size  | Weight | Notes                              |
|------------------|-------|--------|------------------------------------|
| Body             | 16px  | 400    | Minimum. Never go below on mobile. |
| Card gym name    | 16px  | 700    |                                    |
| Drawer gym name  | 20px  | 800    |                                    |
| Filter chip      | 13px  | 400    |                                    |
| Badge / label    | 11px  | 700    | Upper-case, 0.5px letter-spacing   |
| Section label    | 11px  | 700    | Upper-case, 0.8px letter-spacing   |
| Card time        | 14px  | 600    |                                    |
| Freshness line   | 11px  | 400    |                                    |

---

## 3. Spacing scale

Values are in pixels. Prefer multiples of 4.

`4 / 6 / 8 / 10 / 12 / 14 / 16 / 20 / 24 / 32 / 40`

---

## 4. Radius scale

| Token        | Value | Used for                             |
|--------------|-------|--------------------------------------|
| `--radius-sm`| 6px   | Inputs, buttons, small badges        |
| `--radius-md`| 10px  | Cards                                |
| `--radius-lg`| 16px  | Drawers, modals, bottom sheet        |

---

## 5. Tap targets

Minimum 44x44px for all interactive elements on mobile. See: WCAG 2.5.5 (AAA, but treat as required for this product given primary mobile use).

Filter chips: 36px height is acceptable because they are navigational aids, not primary actions. All primary buttons, FAB, and card "Details" links must be >= 44px.

---

## 6. Components

### Freshness badge
- Three states: `fresh` (green), `warn` (amber), `stale` (red)
- Colored dot + short label: "Fresh" / "Aging" / "Stale"
- Full human-readable string in `aria-label`: e.g. "Verified 2 days ago by owner"
- Appears on: every gym card (top-right), every map popup, detail drawer
- Color-only distinction is supplemented by label text (accessible)

### Format badge
- Three values: `gi` (blue), `nogi` (purple), `both` (cyan)
- All-caps, 11px, 700 weight
- Appears on: gym card, map popup, schedule rows

### Visitor policy indicator
- Colored dot + text label on card
- Full banner in detail drawer (green/amber/red background strip)

### Map marker
- Teardrop shape (CSS-only, no SVG asset)
- Color matches freshness: green/amber/red
- Default accent orange when no open mat on the selected day

### Filter chips
- Horizontal scroll row, no wrapping
- Toggle behavior: tap to activate (accent border + dim bg), tap again to deactivate
- Format chips are mutually exclusive (radio behavior); visitor and free are independent toggles

### Bottom sheet (mobile)
- Three snap heights: peek (100px), half (45%), full (92%)
- Tap handle to cycle; engineer may add drag gesture
- On desktop (>= 768px): becomes a fixed-width left sidebar (360px)

### Detail drawer
- Mobile: slides up from bottom, overlays map, max-height 94%
- Desktop: slides in from right, 400px wide, full height
- Always shows: policy banner, full schedule, freshness block, contact links, report button

### FAB
- Fixed position, bottom-right
- Accent color background, pill shape
- Opens submit modal

---

## 7. Layout

### Mobile (< 768px)
1. Header (search + filter chips) — fixed at top
2. Map — fills remaining height (absolute, full)
3. Bottom sheet — snaps over map; draggable
4. FAB — fixed over bottom sheet

### Desktop (>= 768px)
1. Header — full width at top
2. Left sidebar (360px) — gym list, scrolls independently
3. Map — fills remaining horizontal space
4. Detail drawer — slides in from right, overlays map only
5. FAB — fixed bottom-right

---

## 8. Accessibility

- Contrast: all foreground/background pairings checked against WCAG AA (4.5:1 for normal text, 3:1 for large text). Dark surface base makes this tractable.
- `aria-label` on all icon-only buttons
- `aria-pressed` on filter chips
- `aria-live="polite"` on result count
- `role="dialog"` + `aria-modal="true"` on drawer and modal
- Focus is moved to close button when drawer opens; to first field when modal opens
- Escape key closes topmost layer
- `role="list"` on gym list; `role="listitem"` on each card
- Map div has `role="region"` with `aria-label`

---

## 9. OSM attribution

Leaflet renders the attribution control automatically. It must remain visible and unobscured at all times. The attribution reads: "© OpenStreetMap contributors" with a link. Do not hide or override `attributionControl: false`.

---

## 10. What is not in scope

- Illustrations or icons beyond inline SVG (12 strokes from the system; no paid icon font)
- Animation beyond CSS transitions (no JS animation libraries)
- Dark/light mode toggle (dark-only for MVP; revisit if users ask)
- Custom typeface loading (system stack only)
