# Layout Archetypes — the page skeleton

This is the axis that was missing. **Mode = paint. Layout = bones.** Two artifacts in the same mode but different layouts look like different products; two in different modes but the same layout look like reskins of one template (which is the exact failure this fights).

Pick a layout **independently** of mode. Then rotate: do not reuse a layout archetype from the last 3 outputs. The default `single-column-scroll` is now just *one of seventeen* — reaching for it by reflex is the bug.

Each entry: the skeleton, how the eye moves, and a CSS scaffold hint. Build the skeleton first, then apply the mode's paint.

---

### 1. `single-column-scroll`
One narrow column, top-to-bottom. **The overused default — use sparingly and only when the content is genuinely linear prose.**
Flow: vertical, linear. Scaffold: `max-width: 70ch; margin: auto`. Reading rhythm must still vary (don't repeat `header→§n→table`).

### 2. `multi-column-newspaper`
True multi-column body text that wraps, masthead across the top, rules between columns. Content flows like a broadsheet.
Flow: down column 1, up to top of column 2. Scaffold: `column-count: 2/3; column-gap; column-rule`. Headlines span columns with `column-span: all`.

### 3. `grid-of-tiles`
Browseable masonry/card grid, no fixed reading order. Each tile self-contained. Good when items are peers (papers, options, entries).
Flow: non-linear, scan-and-pick. Scaffold: `display: grid; grid-template-columns: repeat(auto-fill, minmax(240px,1fr))` or CSS columns for masonry.

### 4. `full-bleed-deck`
Full-viewport sections, one idea per screen, scroll-snap between them. Slide/landing feel. Each section can have its own bg color.
Flow: paged, one screen at a time. Scaffold: `section{min-height:100vh}` + `scroll-snap-type: y mandatory; scroll-snap-align: start`.

### 5. `sidebar-nav-docs`
Fixed sidebar (TOC / meta / nav) + scrolling content pane. Docs-site / reference grammar.
Flow: persistent nav, content scrolls beside it. Scaffold: `display:grid; grid-template-columns: 240px 1fr` with `position: sticky` sidebar.

### 6. `split-screen`
Two fixed halves: visual|text, or A|B, or term|definition. One half can be sticky while the other scrolls.
Flow: cross-reference between halves. Scaffold: `grid-template-columns: 1fr 1fr; height:100vh` with one side `position:sticky`.

### 7. `poster-asymmetric`
**No scroll.** Everything on one screen, composed asymmetrically with a strong focal point and deliberate negative space. Print-poster discipline.
Flow: focal point → supporting elements by size/contrast. Scaffold: `height:100vh; display:grid` with a few intentionally unequal areas (`grid-template-areas`). Big type does the work.

### 8. `timeline-spine`
A literal vertical (or horizontal) spine with events/items hung off alternating sides or one rail.
Flow: along the spine. Scaffold: a central `::before` line; items as grid rows alternating `justify-self`.

### 9. `magazine-spread`
Two-page-spread feel: a center gutter, unequal column widths, pull-quotes breaking the grid, image wells, a drop-cap opener.
Flow: editorial — eye jumps between lede, pull-quote, body. Scaffold: asymmetric grid (`grid-template-columns: 1.4fr 1fr`), elements that span/break out of the text column.

### 10. `card-stack-dossier`
Discrete "pages" or "cards" stacked vertically, each a self-contained unit with its own header/stamp/edge — like flipping through a case file or a deck.
Flow: card by card. Scaffold: repeated `.card` blocks with strong individual framing (borders, tabs, paper edges), generous gaps between.

### 11. `dashboard-grid`
Fixed grid of panels/metrics of varying span. Non-scrolling or minimal-scroll control-room view.
Flow: scan tiles by importance. Scaffold: `grid-template-columns: repeat(12,1fr)` with panels spanning `grid-column: span N`; KPI row up top.

### 12. `comparison-matrix-first`
The matrix/table **is** the page — the dominant element, not a supporting one. Rows × columns carry the whole argument.
Flow: read across rows / down columns. Scaffold: a large styled table or CSS grid matrix as the centerpiece, minimal chrome around it.

### 13. `zigzag-alternating-bands`
Full-width horizontal bands that alternate image-left/text-right then image-right/text-left. Marketing/story rhythm.
Flow: down through alternating bands. Scaffold: stacked `section`s, each `grid-template-columns: 1fr 1fr` with order swapped on even bands.

### 14. `radial-centerpiece`
One central object (a map, a diagram, an exploded view, a hero figure) with annotations radiating outward via callout lines.
Flow: center-out. Scaffold: a positioned center element + absolutely-positioned annotations + SVG leader lines. Pairs naturally with transit-map / cad-exploded modes.

### 15. `single-object`
The whole page **is** one rendered object — a ticket, a trading card, a recipe card, a label, a receipt — possibly with a subtle backdrop. Often fixed-size, print-like.
Flow: read the object. Scaffold: one centered fixed-aspect container styled as the physical object (perforations, rounded corners, barcode, seal); the rest of the viewport is backdrop.

### 16. `corkboard-scatter`
Items pinned at slight angles across a textured surface — polaroids, index cards, torn notes — optionally connected by string/leader lines. Deliberately imperfect; the scatter IS the design.
Flow: wander, follow the string. Scaffold: `position:relative` board; children `position:absolute` (desktop) or a loose grid with per-item `transform:rotate(-2.5deg…2deg)` jitter (see imperfection kit in `craft-recipes.md`); SVG overlay for connecting lines. **Must collapse to a sane stacked flow at mobile widths.**

### 17. `horizontal-panorama`
The page scrolls sideways: a filmstrip, a mural, a museum corridor, a timeline you walk along. Rare enough to feel like an event.
Flow: left → right, panel by panel. Scaffold: `display:flex; overflow-x:auto; scroll-snap-type:x mandatory` on a full-height track; panels `flex:0 0 min(90vw,640px); scroll-snap-align:center`. Provide a visible "scroll →" affordance and a vertical fallback under 640px.

---

## Choosing a layout

1. **Format-first.** Itinerary → `single-object` (boarding passes) or `timeline-spine`. Comparison → `comparison-matrix-first` or `split-screen`. Roadmap → `timeline-spine` or `radial-centerpiece`. Manifesto → `poster-asymmetric`. Catalog/options → `grid-of-tiles`. Reference → `sidebar-nav-docs`. Monitoring → `dashboard-grid`. Story/marketing → `zigzag-alternating-bands` or `full-bleed-deck`. Essay → `magazine-spread` or `multi-column-newspaper`. Investigation/personal collage → `corkboard-scatter`. Journey/chronology-as-experience → `horizontal-panorama`.
2. **Rotate.** Drop any layout used in the last 3 outputs.
3. **Reward surprise.** A defensible non-obvious layout (a tax plan as `single-object` receipts; a paper as `dashboard-grid`) beats the safe pick — pick it when it still serves the content.
