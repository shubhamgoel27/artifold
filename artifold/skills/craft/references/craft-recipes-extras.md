# Craft recipes: extras: conditional sections

Section numbers are shared with `craft-recipes.md` (core); a bare "§N" citation resolves across both files. Open this file only when the chosen mode, device, or content calls for one of: **§7 grain · §12 neubrutalism · §13 imperfection kit · §14 hand-drawn SVG · §15 eggs & warmth patterns · §18 chart grammar (any page with a chart) · §19 earned interaction · §20 red string.**

## 7. Grain / noise overlay: kills flatness & gradient banding (CSS-Tricks)
Tasteful band: opacity **.03–.06**.
```css
body::before{ content:""; position:fixed; inset:0; pointer-events:none; z-index:9999; opacity:.04;
 background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
```

## 12. Neubrutalism recipe (when the mode calls for it): 0-blur offset shadow
```css
.brutal{ border:3px solid #000; border-radius:0; background:#ffde59; box-shadow:6px 6px 0 0 #000;
  transition:transform .1s,box-shadow .1s; }
.brutal:active{ transform:translate(3px,3px); box-shadow:3px 3px 0 0 #000; }
```

## 13. Imperfection kit: evidence a human touched the page
Perfect alignment reads machine-made. Warm/diegetic modes want 1–3 of these, placed deliberately (near content they relate to), never sprinkled uniformly.
```css
/* Rotation jitter, deterministic, not random-looking-random */
.pinned:nth-child(3n){ transform:rotate(-1.6deg); }
.pinned:nth-child(3n+1){ transform:rotate(1.1deg); }
.pinned:nth-child(3n+2){ transform:rotate(-0.4deg); }

/* Tape strip across a corner */
.tape{ position:absolute; top:-10px; left:32px; width:88px; height:26px; transform:rotate(-4deg);
  background:rgba(252,246,222,.62); border-left:1px dashed rgba(0,0,0,.08);
  border-right:1px dashed rgba(0,0,0,.08); box-shadow:0 1px 2px rgba(0,0,0,.12); }

/* Coffee ring (place ONE, off to a side) */
.coffee-ring{ position:absolute; width:92px; height:92px; border-radius:50%;
  border:7px solid rgba(139,90,43,.16); filter:blur(.4px); transform:rotate(8deg) scaleY(.94); }

/* Pushpin */
.pin{ position:absolute; top:-7px; left:50%; width:14px; height:14px; border-radius:50%;
  background:radial-gradient(circle at 35% 30%, #ff8f8f, #c0392b 65%);
  box-shadow:0 2px 3px rgba(0,0,0,.35); }

/* Torn paper edge (bottom) */
.torn{ clip-path:polygon(0 0,100% 0,100% calc(100% - 7px),96% 100%,90% calc(100% - 5px),
  82% 100%,73% calc(100% - 8px),61% 100%,52% calc(100% - 4px),40% 100%,
  30% calc(100% - 7px),18% 100%,8% calc(100% - 5px),0 100%); }
```

## 14. Hand-drawn SVG accents: the underline a person would draw
Inline SVG, `stroke-linecap:round`, slightly-off paths. Use the accent color, 2–3px stroke.
```html
<!-- squiggle underline (place under one KEY phrase, not every heading) -->
<svg class="squiggle" viewBox="0 0 200 12" width="200" height="12" aria-hidden="true">
  <path d="M3 8 Q 28 2, 52 7 T 100 6 T 148 8 T 197 5" fill="none"
        stroke="var(--accent)" stroke-width="3" stroke-linecap="round"/></svg>
<!-- circled word: wrap the word, position the ellipse behind it -->
<svg viewBox="0 0 120 44" aria-hidden="true"><ellipse cx="60" cy="22" rx="56" ry="18"
  fill="none" stroke="var(--accent)" stroke-width="2.5"
  transform="rotate(-2 60 22)" stroke-dasharray="290" stroke-dashoffset="8"/></svg>
```
Optional draw-on effect (guard reduced-motion): animate `stroke-dashoffset` from path length → 0, once, 600ms, on first view.

## 15. Easter eggs & warmth: patterns (the rules live in SKILL.md section 7)
```css
/* Hover-reveal margin confession */
.aside{ border-bottom:1px dotted var(--accent); cursor:help; position:relative; }
.aside:hover::after, .aside:focus-visible::after{ content:attr(data-psst); position:absolute;
  left:0; top:100%; margin-top:6px; padding:8px 12px; background:var(--ink); color:var(--bg);
  font-size:.85rem; border-radius:4px; width:max-content; max-width:34ch; z-index:5; }
/* Selection color as a tiny signature */
::selection{ background:var(--accent); color:var(--bg); }
```
Cheap warmth wins: a real P.S. line · a colophon ("made for <name>, <date>, listening to <x>") · `<title>` that's a sentence, not a label · one footnote that talks back.

## 18. Chart grammar: a wrong chart is worse than no chart
Pick the form by the job, not by decoration:
comparison → **sorted horizontal bars** · trend → **line** · part-of-whole → **stacked bar** (pie only ≤4 slices) · distribution → **dot plot / histogram** · relationship → **scatter** · one KPI → **big number** + context line · before/after pairs → **slope chart**.

Integrity rules, non-negotiable:
- **Bar axes start at 0.** (Line charts may zoom the axis, then say so on the chart.)
- **Sort categories by value**, never alphabetically, unless order is inherent (time, stages).
- **Label data directly** at the end of each bar/line; a legend is a failure of proximity (tolerate one only at 6+ series).
- **One hue for data, gray for context, the accent for THE point.** Never rainbow categoricals.
- **Annotate the takeaway on the chart itself** ("Norway 2–0: the upset"), the reader shouldn't have to derive it.
- **Erase non-data ink** (Tufte): faint or no gridlines, no chart border, no background fill, no 3D, no dual y-axes.
- Real data only, if a value is unknown, show the gap honestly, never invent a plausible bar.
- **A rule stated in the caption must be drawn in the plot.** If the copy names a threshold, membership cut, or grouping, the chart shows it: a faint dotted rule at the value plus a distinct treatment (halo, ring, brightened fill) on the qualifying marks.
- **Every bar shares one scale, at every width.** Put value labels in their own grid column, never inside the flex row that holds the segments: a wider label squeezes its own row, and on a phone the biggest value can draw as the shortest bar. Set `flex: 0 0 auto` on segments. (Caught live: a $705K bar rendered shorter than a $590K one at 375 px.)
- **In-plot annotations need a mobile plan.** SVG labels shrink with the SVG and turn to lint under ~640px. Pattern: class the in-plot `<text>` as `.anno`, hide `.anno` below 640px, and put an HTML key line in the figcaption shown only at that width. (For dense plots, `overflow-x:auto` on a min-width wrapper is the fallback.)

Hand-built inline SVG or CSS bars beat a library aesthetic: `--w: calc(var(--value) / var(--max) * 100%)` on a styled div, `tabular-nums` value labels, one `<text>` annotation.

## 19. Earned interaction: progressive disclosure without tricks
Interaction must pay rent: it hides complexity the first read doesn't need. It never hides core content (egg rules, SKILL.md section 7).
- **`<details>/<summary>`** for appendix-grade depth: zero JS, style the summary like a real element (marker, hover state), write the summary line so skipping it is safe.
- **Tabs** only for true alternatives (plan A/B, platform X/Y) where the reader picks one lane: `aria-selected`, arrow-key support, or the radio-input CSS pattern.
- **Sortable table** only past ~8 rows; tiny inline JS + `aria-sort`.
- **State must be visible**, what's open, active, or sorted should be obvious in a screenshot.
- **No hover-only meaning** (touch exists; hover may *enrich*, never *gate*). No scroll-hijacking, ever. If the page works with JS disabled, you built it right.

## 20. Red string / connection overlay (corkboard layouts)
Full-board SVG overlay, `pointer-events:none`, drawn AFTER layout is fixed. Sag the line with a quadratic curve; end each at a pin dot.
```html
<svg class="strings" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none">
  <path d="M180 220 Q 330 300, 480 190" fill="none" stroke="#d22c2c" stroke-width="2" opacity=".85"/>
  <circle cx="180" cy="220" r="4" fill="#d22c2c"/><circle cx="480" cy="190" r="4" fill="#d22c2c"/>
</svg>
```
Coordinates in a fixed-size board container (scale the whole board, not the strings). Hide strings under 640px when the board stacks.
