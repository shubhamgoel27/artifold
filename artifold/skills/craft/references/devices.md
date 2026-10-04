# Signature Devices: the one thing you actually build

Every artifact must commit to **one** hand-built signature device: the memorable, non-default element a designer would point at and say "that's intentional." It is the antidote to reskinning, even the same layout+mode reads fresh with a different device.

Rules:
- **Exactly one** primary device per artifact (a second, quieter one is fine; three is clutter).
- **Fit first; freshness breaks ties** (SKILL.md section 4).
- **Build it, don't stub it.** A real SVG, a real annotation layer, a real perforated edge, not a `<div class="card">` with a shadow.
- The device should **carry content**, not decorate emptiness.

---

### 1. `hero-dataviz`: a custom SVG chart/diagram
A bespoke chart built for this data: a slope chart, a small-multiples grid, a custom bar/bullet, a node graph. Not a generic library chart, and it must obey the chart grammar (§18, `craft-recipes-extras.md`). *Best for: results, comparisons, trends.*

### 2. `margin-apparatus`: a running rail beside the content
A persistent left/right margin carrying footnotes, a mini-timeline, a progress ticker, citations, or running stats, like a scholarly edition or a film strip. *Best for: dense reference, chronologies.*

### 3. `duotone-image`: a treated photographic layer
Real images pushed through a duotone / halftone / posterize treatment so they belong to the palette. (Extract from a PDF/source when available.) *Best for: anything with real imagery; makes it cohere.*

### 4. `giant-typographic-figure`: type as the main image
One enormous numeral, word, or glyph that dominates the composition and anchors everything else. *Best for: posters, single statements, one big stat.*

### 5. `die-cut-object`: a physical-object frame
Render a real object: perforation tear-line, barcode, rubber stamp, wax seal, foil corner, paper-clip, sticker, receipt edge. *Best for: tickets, cards, labels, kits.*

### 6. `annotation-callout-layer`: leader lines onto a focal object
Circled regions, numbered pins, and leader lines pointing at parts of a central image/diagram, with marginal notes. *Best for: teardowns, how-it-works, maps.*

### 7. `fold-seam-gutter`: a structural crease
A visible fold, spine gutter, or panel seam that organizes the page like a brochure or spread, content reflows around it. *Best for: magazine-spread, brochures, before/after.*

### 8. `isotype-pictograms`: a custom icon system
A small set of hand-built pictograms used consistently to encode categories/quantities (one icon = one unit). Not decorative Lucide icons. **Every pictogram must pass the no-caption test:** cover its caption and ask what the drawing says alone, a circle on a stick is a lollipop until a horizon line and rays make it a sunrise; a rounded rectangle is nothing until a bezel, camera dot, and tilt make it a phone. The disambiguating context marks (ground lines, bezels, motion dashes) are the difference between an icon system and colored shapes. *Best for: stats for general audiences, taxonomies, do/don't procedure cards.*

### 9. `ticker-status-row`: live-instrument readout
A marquee, status-LED strip, departure-board flap row, or scoreboard that reads like a real instrument panel. *Best for: dashboards, schedules, "current state."*

### 10. `hand-sketch-overlay`: drawn marks over clean base
Hand-drawn circles, arrows, underlines, corrections, marginalia layered over otherwise-clean content, the "annotated by a human" look. *Best for: critiques, edits, explainers.*

### 11. `oversized-pull-quote`: a breakout statement
A single line set very large that breaks the column grid and interrupts the read, editorial punctuation. *Best for: essays, narratives, opinion.*

### 12. `exploded-diagram`: separated parts in space
Components pulled apart along an axis with alignment lines, showing how a whole decomposes. *Best for: systems, architectures, assemblies.*

### 13. `easter-egg`: a hidden reward for the curious
One secret that only reveals on interaction: a hover that flips a card to its "back", a footnote that answers back, a title that changes when you select it, a ★ that expands into a confession. Egg rules live in SKILL.md section 7 (reward, never obstruct, leave a scent); patterns in `craft-recipes-extras.md` §15. *Best for: anything, pure delight; pairs with any layout.*

### 14. `physical-clutter`: evidence the page was touched
Tape strips, pushpins, a coffee ring, a paperclip, a torn edge, a sticky note at an angle. Two or three pieces, placed like a person left them (near content they'd plausibly relate to), not sprinkled uniformly. CSS in `craft-recipes-extras.md` §13. *Best for: warm/personal and diegetic modes; corkboard, scrapbook, cookbook.*

### 15. `mascot-doodle`: a recurring hand-drawn character
A tiny SVG creature (a blob, a cat, a paper airplane) that appears 3–5 times reacting to the content: pointing at the good number, sweating at the caveat, sleeping through the boring section. Same character every time, different pose. *Best for: explainers, guides, anything that wants a companion.*

### 16. `kinetic-title`: one title moment that performs
The headline assembles, split-flaps, gets underlined by a drawing hand, or has one word that misbehaves. Exactly one moment, ≤1.5s, `animation-fill-mode:forwards`, fully guarded by `prefers-reduced-motion` (static end-state must read perfectly). *Best for: posters, decks, arrival moments.*

### 17. `colophon`: a human sign-off
A small end-block that breaks the fourth wall: who this was made for, when, in what mood, with what tools, one honest admission ("the third section fought me"). Like a letterpress colophon or a zine's last page. Keep it ≤4 lines and true. *Best for: everything, the cheapest warmth device there is.*

### 18. `red-string`: connections drawn as string
An SVG overlay of taut or slightly-sagging lines (with pin dots) connecting related items across the page, conspiracy-board style. The connections must be REAL relationships in the content, labeled where useful. *Best for: corkboard-scatter layout, investigations, "how X relates to Y."*

### 19. `scroll-scene`: one pinned, scrubbed transformation
A single section pins while scroll scrubs a real transformation: a chart assembling bar by bar, a diagram exploding, a before→after morph, a pipeline lighting up stage by stage. Scroll position IS the timeline, so the reader controls the pace. Rules: **one per page**, `experience` tier only, built per `motion.md` (ScrollTrigger pin+scrub or CSS scroll-driven), and it must degrade to the *completed* state with JS off or reduced-motion on. *Best for: papers with one big mechanism, product stories, anything where the transformation is the point.*

### 20. `stamp-passport`: progress as collected ink
Completed items get a real rubber stamp (dated, rotated 2–8°, occasionally overlapping its box edge like a hurried border agent); pending items are empty dotted outlines waiting. The asymmetry between stamped and blank IS the status display. *Best for: trackers, streaks, checklists, journeys, anything with done/not-done state.*

### 21. `receipt-tape`: the argument, itemized
A running monospace receipt totals the content: costs, hours, calories, wins, regrets. Line items with dotted leaders, then SUBTOTAL / TAX / **TOTAL** where the total line is the page's one-sentence takeaway (the tax line is a great place for a joke or a caveat). Perforated top/bottom edges per §13. *Best for: budgets, retros, year-in-reviews, "what it actually cost."*

### 22. `gauge-cluster`: analog dials at real values
A row of 3–5 SVG analog gauges (needle, tick marks, red zone) reading like a cockpit or a dashboard of an old car, each needle set to a real value from the content. Label plates under each. Needles may sweep once on load (motion-gated); static position must be correct without JS. *Best for: status pages, health metrics, multi-dimension scores.*

### 23. `constellation-chart`: data as a named night sky
Items become stars on a dark field (size = magnitude of something real), true relationships drawn as thin constellation lines, and the shape is *named* like a real constellation ("The Job Hunt, as seen from June"). A small legend plays star-atlas furniture. *Best for: networks with poetry in them, relationship maps, retrospectives.*

### 24. `compare-slider`: a draggable before/after reveal
Two stacked images or rendered states with a drag handle wiping between them (`input[type=range]` driving a `clip-path`, ~10 lines of JS, no library). **JS-off fallback: both states shown side by side, labeled.** *Best for: edits, redesigns, then/now, A vs B.*

### 25. `progression-motif`: one element, repeated, changing state
A single small element recurs in the same position across every section or panel, and its *state* encodes progress through the content: a wave calming panel by panel, a moon filling in, a battery charging, a plant growing, a knot loosening. The repetition proves intent; the progression carries meaning; the final state is the conclusion. Rules: same position every time · the change must map to something real in the content · readable at a glance without a legend. *Best for: journeys, multi-phase plans, panoramas and decks, anything with a before→after arc.*

### 26. `hands-on-toy`: one physical interaction to fidget with
The page contains one working toy that invites touch: a scratch-off panel (canvas + pointer events) hiding the verdict, a pull-tab that slides a detail card out of a sleeve, a tear-off calendar page, draggable stickers, a spin-the-wheel picker that lands on real options, a flip-clock you can flick. Rules: `experience` tier only · ONE toy · whatever the toy hides must also exist in plain sight (or render visible with JS off) · touch targets ≥44px · the toy must operate on the *content* (scratch off the answer, spin between the actual candidates), never pure decoration. *Best for: gifts, reveals, picks-of-the-week, anything with a verdict.*

---

## Choosing a device
1. **What's the content's natural hero?** Numbers → `hero-dataviz` / `giant-typographic-figure` / `gauge-cluster`. An object → `die-cut-object`. A process/network → `exploded-diagram` / `annotation-callout-layer` / `constellation-chart`. Imagery → `duotone-image` / `compare-slider`. Argument → `oversized-pull-quote`. Connections → `red-string` / `constellation-chart`. Progress/state → `stamp-passport` / `progression-motif`. Totals/accounting → `receipt-tape`. Warmth wanted → `colophon` / `mascot-doodle` / `physical-clutter`. Pure delight → `easter-egg` / `kinetic-title` / `hands-on-toy` (experience tier).
2. **Fit first; freshness breaks ties** (SKILL.md section 4).
3. **Devices 13–17 stack differently:** they're light enough to be the *quieter second device* alongside a structural primary (e.g. `hero-dataviz` + `colophon`; `annotation-callout-layer` + `easter-egg`). A warm page usually wants one structural device + one human one.
4. **Pair, don't duplicate, the layout.** The device should add a dimension the layout doesn't already provide (e.g., `radial-centerpiece` layout + `annotation-callout-layer` device = coherent; `dashboard-grid` layout + `ticker-status-row` device = coherent).
