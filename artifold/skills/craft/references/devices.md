# Signature Devices — the one thing you actually build

Every artifact must commit to **one** hand-built signature device: the memorable, non-default element a designer would point at and say "that's intentional." It is the antidote to reskinning — even the same layout+mode reads fresh with a different device.

Rules:
- **Exactly one** primary device per artifact (a second, quieter one is fine; three is clutter).
- **Rotate:** don't reuse a device class from the last 2 outputs.
- **Build it, don't stub it.** A real SVG, a real annotation layer, a real perforated edge — not a `<div class="card">` with a shadow.
- The device should **carry content**, not decorate emptiness.

---

### 1. `hero-dataviz` — a custom SVG chart/diagram
A bespoke chart built for this data: a slope chart, a small-multiples grid, a custom bar/bullet, a node graph. Not a generic library chart. *Best for: results, comparisons, trends.*

### 2. `margin-apparatus` — a running rail beside the content
A persistent left/right margin carrying footnotes, a mini-timeline, a progress ticker, citations, or running stats — like a scholarly edition or a film strip. *Best for: dense reference, chronologies.*

### 3. `duotone-image` — a treated photographic layer
Real images pushed through a duotone / halftone / posterize treatment so they belong to the palette. (Extract from a PDF/source when available.) *Best for: anything with real imagery; makes it cohere.*

### 4. `giant-typographic-figure` — type as the main image
One enormous numeral, word, or glyph that dominates the composition and anchors everything else. *Best for: posters, single statements, one big stat.*

### 5. `die-cut-object` — a physical-object frame
Render a real object: perforation tear-line, barcode, rubber stamp, wax seal, foil corner, paper-clip, sticker, receipt edge. *Best for: tickets, cards, labels, kits.*

### 6. `annotation-callout-layer` — leader lines onto a focal object
Circled regions, numbered pins, and leader lines pointing at parts of a central image/diagram, with marginal notes. *Best for: teardowns, how-it-works, maps.*

### 7. `fold-seam-gutter` — a structural crease
A visible fold, spine gutter, or panel seam that organizes the page like a brochure or spread — content reflows around it. *Best for: magazine-spread, brochures, before/after.*

### 8. `isotype-pictograms` — a custom icon system
A small set of hand-built pictograms used consistently to encode categories/quantities (one icon = one unit). Not decorative Lucide icons. *Best for: stats for general audiences, taxonomies.*

### 9. `ticker-status-row` — live-instrument readout
A marquee, status-LED strip, departure-board flap row, or scoreboard that reads like a real instrument panel. *Best for: dashboards, schedules, "current state."*

### 10. `hand-sketch-overlay` — drawn marks over clean base
Hand-drawn circles, arrows, underlines, corrections, marginalia layered over otherwise-clean content — the "annotated by a human" look. *Best for: critiques, edits, explainers.*

### 11. `oversized-pull-quote` — a breakout statement
A single line set very large that breaks the column grid and interrupts the read — editorial punctuation. *Best for: essays, narratives, opinion.*

### 12. `exploded-diagram` — separated parts in space
Components pulled apart along an axis with alignment lines, showing how a whole decomposes. *Best for: systems, architectures, assemblies.*

### 13. `easter-egg` — a hidden reward for the curious
One secret that only reveals on interaction: a hover that flips a card to its "back", a footnote that answers back, a title that changes when you select it, a ★ that expands into a confession. Rules: it must **reward** (a real extra fact or joke), never **obstruct** (no content locked behind it), and leave a faint scent (a subtle affordance so it's findable). *Best for: anything — this is pure delight; pairs with any layout.*

### 14. `physical-clutter` — evidence the page was touched
Tape strips, pushpins, a coffee ring, a paperclip, a torn edge, a sticky note at an angle. Two or three pieces, placed like a person left them (near content they'd plausibly relate to), not sprinkled uniformly. CSS recipes in `craft-recipes.md`. *Best for: warm/personal and diegetic modes; corkboard, scrapbook, cookbook.*

### 15. `mascot-doodle` — a recurring hand-drawn character
A tiny SVG creature (a blob, a cat, a paper airplane) that appears 3–5 times reacting to the content: pointing at the good number, sweating at the caveat, sleeping through the boring section. Same character every time, different pose. *Best for: explainers, guides, anything that wants a companion.*

### 16. `kinetic-title` — one title moment that performs
The headline assembles, split-flaps, gets underlined by a drawing hand, or has one word that misbehaves. Exactly one moment, ≤1.5s, `animation-fill-mode:forwards`, fully guarded by `prefers-reduced-motion` (static end-state must read perfectly). *Best for: posters, decks, arrival moments.*

### 17. `colophon` — a human sign-off
A small end-block that breaks the fourth wall: who this was made for, when, in what mood, with what tools, one honest admission ("the third section fought me"). Like a letterpress colophon or a zine's last page. Keep it ≤4 lines and true. *Best for: everything — the cheapest warmth device there is.*

### 18. `red-string` — connections drawn as string
An SVG overlay of taut or slightly-sagging lines (with pin dots) connecting related items across the page, conspiracy-board style. The connections must be REAL relationships in the content, labeled where useful. *Best for: corkboard-scatter layout, investigations, "how X relates to Y."*

---

## Choosing a device
1. **What's the content's natural hero?** Numbers → `hero-dataviz` or `giant-typographic-figure`. An object → `die-cut-object`. A process/network → `exploded-diagram` / `annotation-callout-layer`. Imagery → `duotone-image`. Argument → `oversized-pull-quote`. Connections → `red-string`. Warmth wanted → `colophon` / `mascot-doodle` / `physical-clutter`. Pure delight → `easter-egg` / `kinetic-title`.
2. **Rotate** off the last 2 device classes.
3. **Devices 13–17 stack differently:** they're light enough to be the *quieter second device* alongside a structural primary (e.g. `hero-dataviz` + `colophon`; `annotation-callout-layer` + `easter-egg`). A warm page usually wants one structural device + one human one.
4. **Pair, don't duplicate, the layout.** The device should add a dimension the layout doesn't already provide (e.g., `radial-centerpiece` layout + `annotation-callout-layer` device = coherent; `dashboard-grid` layout + `ticker-status-row` device = coherent).
