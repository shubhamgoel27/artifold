# Layout Archetypes: the page skeleton

**Layout = bones** (mode is only paint). Pick it **independently** of mode; fit first, freshness breaks ties (SKILL.md section 4). The default `single-column-scroll` is just *one of twenty-five*, reaching for it by reflex is the bug.

Each entry: the skeleton, how the eye moves, and a CSS scaffold hint. Build the skeleton first, then apply the mode's paint.

---

### 1. `single-column-scroll`
One narrow column, top-to-bottom. **The overused default, use sparingly and only when the content is genuinely linear prose.**
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
Flow: editorial, eye jumps between lede, pull-quote, body. Scaffold: asymmetric grid (`grid-template-columns: 1.4fr 1fr`), elements that span/break out of the text column.

### 10. `card-stack-dossier`
Discrete "pages" or "cards" stacked vertically, each a self-contained unit with its own header/stamp/edge, like flipping through a case file or a deck.
Flow: card by card. Scaffold: repeated `.card` blocks with strong individual framing (borders, tabs, paper edges), generous gaps between.

### 11. `dashboard-grid`
Fixed grid of panels/metrics of varying span. Non-scrolling or minimal-scroll control-room view.
Flow: scan tiles by importance. Scaffold: `grid-template-columns: repeat(12,1fr)` with panels spanning `grid-column: span N`; KPI row up top.

### 12. `comparison-matrix-first`
The matrix/table **is** the page, the dominant element, not a supporting one. Rows × columns carry the whole argument.
Flow: read across rows / down columns. Scaffold: a large styled table or CSS grid matrix as the centerpiece, minimal chrome around it.

### 13. `zigzag-alternating-bands`
Full-width horizontal bands that alternate image-left/text-right then image-right/text-left. Marketing/story rhythm.
Flow: down through alternating bands. Scaffold: stacked `section`s, each `grid-template-columns: 1fr 1fr` with order swapped on even bands.

### 14. `radial-centerpiece`
One central object (a map, a diagram, an exploded view, a hero figure) with annotations radiating outward via callout lines.
Flow: center-out. Scaffold: a positioned center element + absolutely-positioned annotations + SVG leader lines. Pairs naturally with transit-map / cad-exploded modes.

### 15. `single-object`
The whole page **is** one rendered object, a ticket, a trading card, a recipe card, a label, a receipt, possibly with a subtle backdrop. Often fixed-size, print-like.
Flow: read the object. Scaffold: one centered fixed-aspect container styled as the physical object (perforations, rounded corners, barcode, seal); the rest of the viewport is backdrop.

### 16. `corkboard-scatter`
Items pinned at slight angles across a textured surface, polaroids, index cards, torn notes, optionally connected by string/leader lines. Deliberately imperfect; the scatter IS the design.
Flow: wander, follow the string. Scaffold: `position:relative` board; children `position:absolute` (desktop) or a loose grid with per-item `transform:rotate(-2.5deg…2deg)` jitter (imperfection kit, `craft-recipes-extras.md` §13); SVG overlay for connecting lines. **Must collapse to a sane stacked flow at mobile widths.**

### 17. `horizontal-panorama`
The page scrolls sideways: a filmstrip, a mural, a museum corridor, a timeline you walk along. Rare enough to feel like an event.
Flow: left → right, panel by panel. Scaffold: `display:flex; overflow-x:auto; scroll-snap-type:x mandatory` on a full-height track; panels `flex:0 0 min(90vw,640px); scroll-snap-align:center`. Provide a visible "scroll →" affordance (make it first-class: high contrast, count the panels) and a vertical fallback under 640px. **Panels are frames of one filmstrip:** reserve a fixed header-zone height (e.g. `h2{min-height:2.4em}`) so bands, horizons, and footers align across every panel, and pin any recurring bottom element with `margin-top:auto`, without this the strip visibly jitters as you scroll.

### 18. `scrolly-stepper`
The NYT-scrollytelling grammar: a sticky graphic pane while short text steps scroll past it, and each step transforms the graphic (highlights a region, advances a chart, swaps a state). Distinct from `split-screen`: the pinned half *changes* as steps pass.
Flow: read a step, watch the graphic respond, scroll on. Scaffold: `grid-template-columns: 1fr 1.2fr`; graphic `position:sticky; top:0; height:100vh`; steps as tall sections driving state via IntersectionObserver or CSS scroll-driven animation. **JS-off fallback: all graphic states render stacked inline.** `read`+ tier; see `motion.md`.

### 19. `chat-thread`
The page is a conversation: alternating bubbles, timestamps, a typing indicator, maybe an image drop. The reader eavesdrops on the content explaining itself.
Flow: linear, down the thread. Scaffold: flex column; `.msg{max-width:62%}` with `align-self` alternating; sender labels + timestamps as furniture. Pairs naturally with `group-chat` or `oral-history` voice.

### 20. `calendar-grid`
A real month or week grid; the content lives in day cells. Empty days stay empty, the blankness is texture, not failure.
Flow: scan by date, dwell on marked days. Scaffold: `grid-template-columns:repeat(7,1fr)`; day numerals as folios; one hero day can span or pop. **Collapse to an agenda list under 640px.**

### 21. `quadrant-map`
A 2×2 plane where **position is the argument**: effort×impact, cost×joy, risk×upside. Items plotted as dots or mini-cards at coordinates that mean something.
Flow: read the axes first, then quadrant by quadrant. Scaffold: `position:relative` square with labeled axes (`::before/::after` rules); items absolutely positioned from data; quadrant corner labels. Mobile: four stacked quadrant lists.

### 22. `tabbed-binder`
A physical binder or folder with divider tabs sticking out of the edge; one section visible at a time. The tab row is the table of contents.
Flow: pick a tab, read a section. Scaffold: CSS-only radio-input tabs (works with JS off) styled as physical index tabs (offset, layered, slightly rotated); the active tab's card sits "on top" of the stack.

### 23. `branching-path`
A choose-your-own-adventure skeleton: a question node, then routes diverge down the page along drawn connectors. The reader follows *their* branch.
Flow: decide at each fork. Scaffold: decision nodes + SVG connector lines; anchor links jump between branches; every branch also reads sanely straight through top-to-bottom (the no-interaction fallback).

### 24. `accordion-index`
The page loads as a dense collapsed ledger, one-line rows with dotted leaders and folio numbers, like a book's index, and each row expands in place. Disclosure-first design.
Flow: scan the whole index in ten seconds, open only what you care about. Scaffold: styled `<details>/<summary>` rows; **every `summary` line carries a real one-line answer** so the collapsed page is already useful, not a wall of teasers.

### 25. `orbit-rings`
Concentric rings around a nucleus: the core idea at center, items placed on rings by a distance that means something (priority, time horizon, certainty, intimacy). Distinct from `radial-centerpiece`: no callout lines onto one object, ring *membership* is the data.
Flow: center outward, ring by ring. Scaffold: nested circles (or one SVG) with items positioned on ring paths; a legend naming what distance encodes. Mobile: ring-by-ring stacked lists.

---

## Choosing a layout

1. **Format-first.** Itinerary → `single-object` (boarding passes) or `timeline-spine`. Comparison → `comparison-matrix-first`, `split-screen`, or `quadrant-map`. Roadmap → `timeline-spine`, `radial-centerpiece`, or `orbit-rings`. Manifesto → `poster-asymmetric`. Catalog/options → `grid-of-tiles`. Reference → `sidebar-nav-docs`, `tabbed-binder`, or `accordion-index` (FAQ-shaped). Monitoring → `dashboard-grid`. Story/marketing → `zigzag-alternating-bands` or `full-bleed-deck`. Story-with-data → `scrolly-stepper`. Essay → `magazine-spread` or `multi-column-newspaper`. Investigation/personal collage → `corkboard-scatter`. Journey/chronology-as-experience → `horizontal-panorama`. Dialogue/debate/explainer-as-banter → `chat-thread`. Schedule/habit/streak → `calendar-grid`. Decision guide → `branching-path`.
2. **Freshness breaks ties** (SKILL.md section 4), and if your last few picks all came from #1–#12, give #13–#25 first refusal.
3. **Reward surprise.** A defensible non-obvious layout beats the safe pick when it still serves the content.
