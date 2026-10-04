# Craft recipes: the copy-paste CSS that separates pro from amateur

Drop-in techniques. Most AI output skips all of these and looks flat/cheap as a result. Apply the ones the chosen mode calls for (honor its restraint budget). Sourced from Refactoring UI, Josh Comeau, Tobias Ahlin, Utopia, Open Color, Radix, Material.

**Conditional sections live in `craft-recipes-extras.md`** (§ numbers shared; a bare "§N" resolves across both files): §7 grain · §12 neubrutalism · §13 imperfection kit · §14 hand-drawn SVG · §15 egg patterns · §18 chart grammar · §19 earned interaction · §20 red string. Open it only when the mode/device/chart calls for one.

---

## 1. Type scale: one ratio, not eyeballed sizes
Pick ONE ratio: **1.2** (minor third, dense UI) · **1.25** (major third, safe default) · **1.333** (perfect fourth, editorial drama) · **1.5/1.618** (hero-heavy). Multiply from a 1rem base.
```css
:root{ /* 1.25 */
  --step--1:.8rem; --step-0:1rem; --step-1:1.25rem; --step-2:1.563rem;
  --step-3:1.953rem; --step-4:2.441rem; --step-5:3.052rem;
}
h1{ line-height:1.1; letter-spacing:-.02em; }
p{ line-height:1.6; }            /* body 1.5–1.65, headings 1.05–1.2 */
```

## 2. Fluid type & space: clamp() instead of breakpoints (Utopia)
```css
--step-0: clamp(1rem, 0.92rem + 0.42vw, 1.25rem);
h1{ font-size: clamp(2.5rem, 1.5rem + 5vw, 4.5rem); }
section{ padding-block: clamp(3rem, 1.5rem + 7vw, 7rem); }
```

## 3. Spacing scale: one set, base 4px (kills the 13px/19px/27px look)
```css
:root{ --s-1:.25rem; --s-2:.5rem; --s-3:.75rem; --s-4:1rem; --s-6:1.5rem;
       --s-8:2rem; --s-12:3rem; --s-16:4rem; --s-24:6rem; }
```
Whitespace is the cheapest luxury signal, default to more than feels necessary.

## 4. Layered shadows: the "expensive UI" depth trick (Tobias Ahlin / Comeau)
Never a single flat `0 4px 6px rgba(0,0,0,.1)` (that's a slop tell). Stack layers; **tint toward the bg hue**, not pure black; pick ONE light source (above), higher elevation = bigger offset + bigger blur + LOWER opacity.
```css
:root{ --shadow-color:220 40% 25%; }
--shadow-sm:0 1px 2px hsl(var(--shadow-color)/.16);
--shadow-md:0 2px 4px hsl(var(--shadow-color)/.12), 0 6px 12px hsl(var(--shadow-color)/.10);
--shadow-lg:0 4px 8px hsl(var(--shadow-color)/.10), 0 16px 28px hsl(var(--shadow-color)/.08);
```

## 5. Color systems: borrow, don't invent (LLMs invent muddy palettes)
**Open Color** 10-step (drop-in neutrals + accents):
```
gray  #f8f9fa #f1f3f5 #e9ecef #dee2e6 #ced4da #adb5bd #868e96 #495057 #343a40 #212529
blue  #e7f5ff #d0ebff #a5d8ff #74c0fc #4dabf7 #339af0 #228be6 #1c7ed6 #1971c2 #1864ab
red   #fff5f5 #ffe3e3 #ffc9c9 #ffa8a8 #ff8787 #ff6b6b #fa5252 #f03e3e #e03131 #c92a2a
```
**Dominance ratio:** one color = 60–70% of visual weight, 1–2 supporting tones, ONE sharp accent. Never equal-weight. **Body text never pure `#000`**, use `#1a1a1a`/Open-Color gray-9.
**Palette specificity test:** if swapping your palette into an unrelated topic would still "work," it's not specific enough.
If generating a custom ramp (Refactoring UI): bump **saturation** as shades approach light/dark extremes, or they wash out.
Prefer `oklch()` for perceptually-even custom ramps when you do roll your own.

## 6. Dark mode done right (Material)
```css
--bg:#121212;                              /* not #000 */
--surface-1:#1e1e1e; --surface-2:#232323; --surface-3:#272727;  /* higher = lighter, not shadowed */
--text:#e6e6e6; --text-dim:#a8a8a8;        /* off-white, never #fff on large areas */
```
Desaturate accent colors (~−15% S) vs light mode so text clears 4.5:1 and colors don't vibrate.

## 8. Motion tokens: lock durations/easings as variables
Animate only `transform`/`opacity`; durations, the effect ladder, and the slop list live in `references/motion.md` (canonical). **Always guard reduced-motion.**
```css
:root{ --ease-out:cubic-bezier(.16,1,.3,1); --ease-spring:cubic-bezier(.34,1.56,.64,1); --dur:280ms; }
@media (prefers-reduced-motion:reduce){
  *{ animation-duration:.01ms!important; animation-iteration-count:1!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
```

## 9. Separation without borders (Refactoring UI)
Borders are a crutch. Prefer (a) a shadow, (b) a background shift between adjacent surfaces, or (c) more spacing. If you must border, use a **tinted faint** one, not gray `#ddd`.
```css
.card{ background:#fff; box-shadow:var(--shadow-md); }          /* not border:1px solid #ddd */
.card--hair{ outline:1px solid rgb(0 0 0 / .06); }              /* tinted, faint */
```

## 10. Optical alignment & tracking (the invisible pro tells)
```css
.eyebrow{ text-transform:uppercase; letter-spacing:.08em; font-weight:600; }  /* caps need tracking */
h1{ letter-spacing:-.02em; }                                                  /* large display tightens */
.prose{ max-width:65ch; line-height:1.6; color:#1a1a1a; }                     /* 60–75ch measure */
```
`text-wrap:balance` on headings, `text-wrap:pretty` on body, free typographic finish.

## 11. Sized image placeholders: no layout shift, real alt text
Self-contained files must not reference missing local images. Reserve the box with an inline SVG sized to the exact W×H, or `https://picsum.photos/seed/<x>/<W>/<H>`.
```html
<img width="640" height="360" alt="<descriptive>" src="https://picsum.photos/seed/k/640/360">
```

## 16. Typographic finish: typeset, don't type
The strongest single human tell. Machine output uses typewriter ASCII; designers use real characters. Do a find-and-replace pass on your copy before shipping (canonical scan one-liner in `references/verify.md`).

| Typed | Typeset | Where |
|---|---|---|
| `"x"` `'x'` | “x” ‘x’ | all quotes |
| `it's` | it’s | all apostrophes |
| `...` | … | ellipsis |
| `2 x 3` | 2 × 3 | dimensions, multiplication |
| `-5%` | −5% | negative numbers (minus, not hyphen) |
| `9-5`, `Jun 11-Jul 19` | 9–5, Jun 11–Jul 19 | ranges (en dash) |
| `40 kg`, `7 h` | 40&nbsp;kg, 7&nbsp;h | a number and its unit never wrap apart; a percent sign attaches with no space (98%) |
| `(c) 2026` | © 2026 | legal marks |
| `No. 7` | № 7 | numero, where the mode suits |

```css
/* columns of figures align; prose figures stay proportional */
table, .stat, .price{ font-variant-numeric: tabular-nums; }
h1,h2,h3{ text-wrap:balance; }
p{ text-wrap:pretty; }
blockquote{ hanging-punctuation: first; }   /* progressive enhancement */
.prose sup{ font-variant-position: super; } /* real superscripts where supported */
```
Optical alignment: hang quote marks and bullets into the margin (`text-indent:-0.45em` on the first line of a blockquote); align numerals, not cell edges, in tables (right-align figures).

## 17. Page furniture: the difference between edited and emitted
Human-made documents carry supporting apparatus; AI pages are furniture-poor. Every artifact should carry the furniture its format would really have:

- **Every figure/chart: a caption** (in-voice, says what to notice, not what it is) **and a source line** (`Source: FIFA, Jul 6 2026`, small, quiet, real).
- **Every quote: an attribution.** Every stat: where it came from. Every screenshot: what it shows.
- **Folios & running heads** for paged/spread layouts (page numbers, a running title in the header/footer).
- **Kickers, deks, bylines, datelines** for editorial layouts (the NYT doesn't publish a bare `<h1>`).
- **Section enders** where the mode suits: a fleuron ❦, a small rule, a tab marker, one, consistent.
- **Meta furniture:** a `<title>` that's a sentence; an inline-SVG favicon in the page palette (2 lines, no file); a visible last-updated date on anything time-sensitive. On factual utility pages, make verification visible: a "rules verified <date>" plate or revision line, in-voice.

Furniture must be real (true sources, honest dates), quiet (a step or two below body text), and consistent (one caption style, used everywhere). Two pieces of true furniture beat six decorative ones.

---

### Defaults (the bans live in SKILL.md section 9)
Distinctive type pairing · a real layered shadow system · varied or zero radius · asymmetric / non-3-column layouts · whitespace over decoration.
