# `/craft` — Design Research

Principles for HTML artifacts that don't read as AI slop. Every rule traces to a real source.

---

## Section 1 — Core Principles

### 1. Hierarchy via weight and color, not size
**Rule:** Don't reach for `text-4xl` to make something important. Use 2 colors (dark primary, mid-grey secondary) and 2 weights (400/500 + 600/700).
**Why:** Size-only hierarchy produces hero-text-in-five-sizes pages that feel shouty and undesigned.
**Applied:** Cap distinct font sizes at 4–5. Vary `font-weight` and `text-color` first; size last.
**Source:** Refactoring UI, "7 Practical Tips for Cheating at Design" (Wathan/Schoger, Medium).

### 2. Start with too much whitespace
**Rule:** Generous spacing signals confidence. Marketing-grade sections use 96–128px vertical padding.
**Why:** Cramped layouts read as cheap/template-y; whitespace is the cheapest premium signal you have.
**Applied:** On a single-page artifact, set section vertical padding ≥ 80px. Don't fill the viewport because it's there.
**Source:** Refactoring UI ("Layout and Spacing"); Vercel/Geist spacing system (Seedflip breakdown).

### 3. Define shades up front, never on the fly
**Rule:** Pick a fixed palette of greys (8–10 steps) and an accent (5–10 shades). No ad-hoc `#a3b2c4` mid-page.
**Why:** Reaching for new hexes mid-build is what gives AI output its "timid, evenly-distributed" feel.
**Applied:** Declare CSS custom properties for the full ramp at the top of the `<style>` block. Use only those.
**Source:** Refactoring UI, "Building Your Color Palette" (free chapter, refactoringui.com).

### 4. Color carries meaning, or it doesn't appear
**Rule:** Greyscale by default. Accent color only on the primary action, a status indicator, or one chart series.
**Why:** Decorative color is the #1 tell of unguided AI output (purple gradient, pastel rainbow accents).
**Applied:** If you could delete every colored pixel and the artifact still parsed, that's the goal. One accent, used 1–3 times.
**Source:** Vercel/Geist ("color appears only when it carries meaning"); Linear method ("simple first, then powerful").
**Disagreement note:** Refactoring UI says "you need more colors than you think" (shade-wise). Geist says fewer hues. Both agree: many shades of few hues, never the inverse.

### 5. Tighten display type letter-spacing
**Rule:** Large headlines need negative tracking (`-0.02em` to `-0.04em`) and tight line-height (~1.1).
**Why:** Default browser letter-spacing on a 48px+ headline makes it look "30% less intentional."
**Applied:** Any heading ≥ 32px gets `letter-spacing: -0.02em; line-height: 1.1`. Body stays default.
**Source:** Vercel/Geist typography rules (Seedflip).

### 6. Offset shadows, don't blur them into blobs
**Rule:** Shadows simulate a light source from above — use vertical offset, modest blur, low opacity.
**Why:** Big symmetric blurs read as 2021-era glassmorphism / generic SaaS card.
**Applied:** `box-shadow: 0 4px 12px rgba(0,0,0,0.06)` over `0 0 40px rgba(...)`. Skip shadows entirely on flat layouts.
**Source:** Refactoring UI, "7 Practical Tips" (offset shadows).

### 7. Borders are a last resort
**Rule:** Before adding a 1px border, try a background-color shift, spacing, or shadow.
**Why:** Borders everywhere creates the "shadcn-default card" look that's now an AI tell.
**Applied:** No more than one border treatment per artifact. Prefer subtle bg shifts (`grey-50` on `white`) to delineate.
**Source:** Refactoring UI ("Use fewer borders").

### 8. Don't enlarge small icons
**Rule:** Icons drawn at 16–24px look amateur scaled to 64px. Put them in a colored shape instead.
**Why:** Giant lucide/feather icons in feature cards is canonical AI-slop signature.
**Applied:** Keep functional icons at native size. For "feature card" decoration, enclose a small icon in a tinted rounded square. Better yet: skip the icon.
**Source:** Refactoring UI, "7 Practical Tips."

### 9. Opinionation over flexibility
**Rule:** Make one strong design choice and commit. Don't hedge with three layout variants on one page.
**Why:** Linear's thesis: "flexible software creates chaos." Same applies to a single artifact — one POV beats five.
**Applied:** Pick one structural motif (e.g. left-rail labels with right-side content, OR full-bleed sections, OR a data-dense table). Don't mix three.
**Source:** Linear, "Method — Introduction" (purpose-built, opinionated).

### 10. Density when the content earns it
**Rule:** Information-rich artifacts (dashboards, comparisons) should be *dense*, not whitespace-padded.
**Why:** Whitespace-heavy is the default AI mode. A real designer adjusts density to content — Bloomberg terminal, not landing-page hero.
**Applied:** If the artifact is a report/dashboard, tighten row spacing, use 13–14px body, lean on tables. Reserve generous whitespace for narrative/marketing artifacts.
**Source:** "Claude Design without the AI-slop look" (TheAdpharm); contrast with Geist's marketing whitespace.

### 11. Type scale ≥ a real ratio, not eyeballed
**Rule:** Use a defined scale (e.g. 12/14/16/20/24/32/48/64) — not "whatever feels right" per element.
**Why:** Eyeballed sizes accumulate into 9 distinct font-sizes across one page, which is the #1 visible amateur tell.
**Applied:** Declare the scale in CSS vars. Every `font-size` references a var. Hard cap: 6 distinct sizes.
**Source:** Refactoring UI ("Designing Text" — establish a type scale).

### 12. Avoid pure black and pure grey-on-color
**Rule:** Use near-black (`#111`–`#1a1a1a`) for text on white. Never grey text on a colored bg — tint the bg's hue instead.
**Why:** Pure black is harsh and screen-flat; mid-grey on color looks washed-out and accidentally low-contrast.
**Applied:** Body text: `#1a1a1a` on white. On a colored panel, text should be a tinted version of that color (or white with reduced opacity).
**Source:** Refactoring UI ("Avoid Pure Black"; "Don't use grey text on colored backgrounds").

---

## Section 2 — Anti-Slop Patterns (avoid these)

1. **Purple/indigo-to-violet gradient hero** with centered eyebrow + 64px headline + subhead + two CTAs. The Lovable/v0 default.
2. **Three or four identical bento cards** in a row, each with a colored-square icon + bold title + grey paragraph.
3. **Inter as the unexamined default font.** If using a sans, justify the choice (Geist, Söhne, Söhne-alternatives, IBM Plex) or own Inter with tight tracking.
4. **Random emoji decoration** on every list item, section header, or bullet. Emojis are punctuation; one per page max, if at all.
5. **Pastel rainbow accent palette** — each section gets its own pastel color "for variety." Reads as crayon box.
6. **Lucide/Feather icons used decoratively** (one per heading, one per list item) with no semantic function.
7. **Glassmorphism panels** — `backdrop-filter: blur` + 10% white bg. Stale since ~2023.
8. **`rounded-2xl` on everything** plus medium drop-shadow plus border. Shadcn-default card in triplicate.
9. **"Section 1 / Section 2 / Section 3" identical rhythm** — every section is `<h2> + paragraph + 3-col grid`. No structural variation.
10. **Hero text in five sizes** stacked: eyebrow 14px, headline 64px, subhead 24px, micro-line 12px, button label 16px. Pick three.
11. **Animated gradient blobs / mesh gradients** in the background. Webflow template circa 2022.
12. **Centered everything.** Real designs use asymmetry; AI defaults center because it's safe.
13. **Generic stock-photo placeholders** (unsplash people-at-laptops) or DALL-E "abstract tech swoosh" hero images.
14. **Pricing-toggle + 3-tier card + FAQ-accordion** triad lifted from every SaaS template.
15. **Times-New-Roman fallback** showing through when the page is meant to read minimal/editorial — declare a real serif (Iowan, Charter, Source Serif) or commit to sans.

**Sources:** TheAdpharm "Claude Design without the AI-slop look"; MindStudio "Avoid generic AI aesthetics."

---

## Section 3 — Self-Check (run before delivering)

1. Is the palette ≤ 2 hues (one neutral ramp + at most one accent), with all shades pre-declared?
2. Does the accent color appear ≤ 3 times, each carrying meaning?
3. Are there ≤ 6 distinct font sizes on the page, all referencing a defined scale?
4. Do headings ≥ 32px have negative letter-spacing and line-height ~1.1?
5. Is hierarchy driven by weight/color first, size second?
6. Is the artifact free of decorative emojis (or capped at 1)?
7. Is the artifact free of decorative icons that add no information?
8. Is there one structural motif, not three layouts competing on one page?
9. If using shadows: offset vertical, low opacity, no symmetric blurs?
10. Is the density appropriate to content type (dense for data, generous for narrative)?
11. Have I avoided the canonical slop combo: centered gradient hero + 3 bento cards + accordion FAQ?
12. Could a designer point at ONE distinctive choice on this page and say "that's intentional"?

---

**Sources consulted:**
- Refactoring UI — refactoringui.com landing, "Building Your Color Palette" free chapter, "7 Practical Tips for Cheating at Design" (Medium), "Top 20 Key Points" summary
- Linear — linear.app/method/introduction
- Vercel/Geist — vercel.com/geist/introduction, Seedflip "Vercel Design System Breakdown"
- AI-slop critiques — theadpharm.com "Claude Design without the AI-slop look", mindstudio.ai "Avoid Generic AI Aesthetics"
