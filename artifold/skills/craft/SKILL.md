---
name: craft
description: Use whenever the user asks for a "report", "dashboard", "one-pager", "explainer", "tracker", "guide", "itinerary", or any HTML artifact where the output is a single styled page. Picks from 15 named design modes (matched to format conventions), enforces a chosen voice register, and refuses 18 named AI-slop signatures — including its own past convergence patterns. If Artifold is installed, reads the library to avoid repeating recent modes.
---

# Craft

You are crafting a high-quality HTML artifact. This is **not** generic "make a report" — apply real design discipline and produce something a designer would call intentional.

The default Claude output for these requests is recognizable AI slop: purple-gradient hero, identical bento cards, decorative emoji on every list item. This skill exists to escape that.

**But the skill itself has a known failure mode** — earlier versions converged on "cream paper + display serif + italic on second noun + uppercase mono eyebrow + rust accent + left-rail grid." That's now its own slop signature. The rules below are designed to fight both.

---

## Step 1: Understand the request

Clarify if not obvious:

- **Topic + audience.** "30-day strength tracker for Annu" vs "explainer for a general audience" lead to different choices.
- **Density signal.** Data-dense report? Narrative explainer? Marketing one-pager?
- **Format convention.** What canonical reference defines the format you're being asked to build? Examples:
  - Tracker → Whoop, Strava, Garmin
  - Tier list → Eater Heatmap, tiermaker.com
  - Technical explainer → Distill.pub, 3Blue1Brown, The Pudding
  - Apartment comparison → Compass / Zillow listing brochure
  - Dashboard → Linear, Vercel, Grafana
  - Field guide → Sibley's Birds, AAA guidebook
  - Itinerary → Wirecutter, NYT Travel
  - Tutorial → MDN, Real Python
  - **Anchor on that reference's visual grammar before reaching for editorial defaults.**
- **Style reference.** Did the user point to a past artifact ("like dobble") or paste an HTML file/URL? That overrides the default mode selection.
- **Constraint.** Printable, mobile-first, one-page, dark only?

If clear, proceed. Don't over-ask.

---

## Step 2: Pick a design mode

Before writing any CSS, **pick a mode**. Available modes and what they look like:

| Mode | Visual language | Good for |
|---|---|---|
| `editorial-newsprint` | warm paper, serif display, mono metadata, single accent, ledger tables | literary essays, wine lists, field reports |
| `swiss-grid` | Helvetica/Inter, strict 12-col grid, generous whitespace, b&w + 1 accent | architectural, museum, design manifestos |
| `technical-blueprint` | graph-paper bg, mono, equations, SVG diagrams, navy/cyan-on-cream | ML/math/CS explainers, technical specs |
| `brutalist-web` | raw HTML defaults, system fonts, no rounded corners, harsh contrast | rebellious, anti-design, indie web |
| `zine-photocopy` | photocopy texture, hand-cut feel, mixed fonts, off-register | personal essays, music writing, scenes |
| `corporate-memo` | Helvetica/Aptos, restrained palette, structured headings | business memos, decision docs, post-mortems |
| `terminal-tui` | monospace everywhere, dark bg + green/amber, box-drawing | dev tools, log viewers, system status |
| `museum-label` | bone-white, small serifed type, lots of breathing room | curated content, single-object focus |
| `field-guide` | illustrated-book vibe, sans display + serif body, watercolor accents | nature guides, taxonomies, catalogs |
| `retro-90s-web` | beveled buttons, Times New Roman, animated gifs, table layout | nostalgic, gaming, fanpages |
| `magazine-fashion` | bold sans display, full-bleed color blocks, big numbers | rankings, tier lists, "best of" lists |
| `data-dashboard` | tight grid of metrics, sparklines, small multiples, monospace numerals | actual dashboards, KPI views, monitoring |
| `softpop-pastel` | warm muted colors, sans, rounded but-not-rounded, illustrated | family-facing, kids, lifestyle |
| `monochrome-poster` | one color + black, big type, asymmetric | manifestos, posters, single-page statements |
| `handwritten-journal` | one handwriting font, blue-ink color, lined-paper bg | personal logs, recipes, casual notes |

### Mode selection rule (apply in this order)

1. **Format-driven.** If Step 1's format-convention anchor exists, use the matching mode.
   - Tier list → `magazine-fashion` (or `corporate-memo` if quiet/serious)
   - Dashboard → `data-dashboard`
   - Math/ML explainer → `technical-blueprint`
   - Itinerary → `field-guide` or `editorial-newsprint`
   - Workout tracker → `spec-sheet`-driven `corporate-memo` or `data-dashboard`
   - Apartment comparison → `corporate-memo` (Compass brochure) or `magazine-fashion`
   - Code/dev-tool readme → `terminal-tui` or `swiss-grid`

2. **Library-driven.** Run `artifold designs --json`. Read the `design_mode` field for each entry (when present). **You may not select any mode used by the most recent 3 /craft outputs.** If a mode appears in 3+ entries total across the library, treat it as "overused" and also avoid.

3. **Tiebreaker.** If multiple modes still qualify after rules 1 and 2, compute `hash(topic_slug) % len(remaining_modes)` and select deterministically.

### Current moratorium

**`editorial-newsprint` is currently overrepresented** in `/craft` outputs. Do not select it unless:
- the topic explicitly demands it (a literary essay, a wine list, a poetry chapbook, a slow-news piece), AND
- no other mode is a reasonable fit, AND
- you write a 1-sentence justification in the artifact's comments.

### User reference overrides

- If the user said *"like dobble"* / *"match my soccer report"*, run `artifold designs --json`, find that entry, then `artifold designs <id> --template` to load CSS + skeleton. **Adapt the structural pattern, but consider rendering it in a different mode** if their library is already heavy in that artifact's mode. Tell the user in 1 sentence what you kept and what you changed.
- If the user pasted HTML, extract the CSS + body skeleton manually and treat the same way.

---

## Step 2.5: Pick a voice register

The chosen register dictates copy tone independently of the visual mode:

| Register | Voice | Headline style |
|---|---|---|
| `lab-notebook` | terse, numbered, second-person imperative | "Day 14. Press 65 lb 5×5." |
| `spec-sheet` | column-aligned facts, zero rhetoric | "AMPS 30. RAM 64GB. Weight 1.4kg." |
| `field-essay` | literary-deadpan, allows comma-pivot italic headlines | "Thirty Days, *Five Lifts*" |
| `coach-imperative` | "do this. don't do that." | "Squat low. Breathe out. Don't rush." |
| `wire-news` | subject-verb-object, dateline, neutral | "SAN FRANCISCO, May 26. Three apartments enter the shortlist." |
| `intimate-letter` | first-person, parenthetical asides | "I lived at 989 20th for a year and (mostly) loved it." |
| `enthusiast` | high-energy, opinion-forward | "Saint Frank is *the* pour-over in Russian Hill. Period." |
| `encyclopedic` | neutral, third-person, present-tense | "Transformers replace recurrent computation with self-attention." |
| `pitch-deck` | claim-evidence-claim | "989 20th wins on commute. Here's why." |

### Hard constraints

- **Comma-pivot italicized-second-clause headlines** (`"X, Y"` with the second part italic) are only legal in `field-essay`. Forbidden in the other 8.
- **Uppercase mono eyebrow** (`FIELD NOTES · NO. 14 · COFFEE`) only legal in `field-essay`, `editorial-newsprint`, or `wire-news`.
- **Em-dashes used as decorative breaks** (`— · —`) — at most one per artifact regardless of register.

---

## Step 3: Apply design principles

These are general principles that hold across all modes. Every one was distilled from real sources.

1. **Hierarchy via weight and color, not size.** Cap distinct font sizes at 4–5. Vary `font-weight` and `text-color` first; size last. *(Refactoring UI)*
2. **Whitespace appropriate to content.** Narrative/marketing → 80px+ section padding. Data-dense → tight rows (this is content-type-specific). *(Refactoring UI, TheAdpharm critique)*
3. **Define shades up front.** Declare CSS custom properties for the full color ramp at the top of `<style>`. *(Refactoring UI free chapter)*
4. **Color carries meaning, or it doesn't appear.** *(Vercel/Geist, Linear)*
5. **Tighten display type** for headings ≥ 32px: `letter-spacing: -0.02em; line-height: 1.1`. *(Vercel/Geist)*
6. **Offset shadows, don't blob.** *(Refactoring UI)*
7. **Borders are a last resort.** *(Refactoring UI)*
8. **Don't enlarge small icons.** *(Refactoring UI)*
9. **Opinionation over flexibility.** One structural motif per artifact. *(Linear method)*
10. **Density when content earns it.** *(TheAdpharm)*
11. **Type scale, not eyeballed sizes.** Cap 6 distinct sizes. *(Refactoring UI)*
12. **Avoid pure black, avoid grey-on-color.** Body text on white: `#111`–`#1a1a1a`. *(Refactoring UI)*

**Mode-specific overrides take precedence.** For example, `brutalist-web` deliberately violates principle 5 (no display-type tracking) and principle 7 (raw borders). `terminal-tui` violates principle 12 (uses pure greens/ambers on near-black). When your chosen mode conflicts with a general principle, the mode wins — and note it in a comment.

---

## Step 4: Anti-slop checklist

Before writing CSS, commit to NOT producing any of these:

1. Purple/indigo-to-violet gradient hero with centered eyebrow + 64px headline + subhead + two CTAs.
2. Three or four identical bento cards in a row with colored-square icons.
3. Inter as the unexamined default font.
4. Random emoji decoration on every list item.
5. Pastel rainbow accents.
6. Lucide/Feather icons used decoratively.
7. Glassmorphism panels.
8. `rounded-2xl` on everything + medium drop-shadow + border.
9. Identical section rhythm (`<h2> + paragraph + 3-col grid`).
10. Hero text in five stacked sizes.
11. Animated gradient blobs / mesh gradients.
12. Centered everything.
13. Generic stock-photo placeholders or DALL-E swooshes.
14. Pricing-toggle + 3-tier card + FAQ-accordion triad.
15. Times-New-Roman fallback in minimal pages.

**The /craft skill has accidentally created these new slop patterns. Treat them as anti-patterns too:**

16. **The /craft signature** — cream paper + display serif + italicized second noun in headline + uppercase mono eyebrow + single rust/oxblood accent + asymmetric left-rail + hairline-rule ledger table. If you find yourself reaching for ANY 3 of these together, you're producing /craft slop. Stop, justify in a comment why this topic demands it over 3 named alternatives, or pick a different mode.
17. **Comma-pivot italicized headline** (`"X, Y"`) — overused. Allowed only in `field-essay` mode.
18. **Uppercase mono eyebrow + serif headline pair** — pick one or the other, not both. (Eyebrow alone is fine; serif headline alone is fine.)

---

## Step 5: Embed Artifold provenance

In the artifact's `<head>`, include:

```html
<meta name="artifold:intent" content="<10–15 word description of what this artifact accomplishes>">
<meta name="artifold:tool" content="claude">
<meta name="artifold:prompt" content="<the user's original prompt, ≤ 200 chars>">
<meta name="artifold:design-mode" content="<the mode you picked from Step 2>">
<meta name="artifold:voice-register" content="<the register you picked from Step 2.5>">
```

If the user referenced a past artifact for style, also add:
```html
<meta name="artifold:style-from" content="<id-of-reference-artifact>">
```

The design-mode and voice-register tags are critical — they're how future /craft runs avoid converging on the same modes you used.

---

## Step 6: Self-check before delivering

1. Did I pick a **design mode** explicitly, and is it appropriate to the format convention from Step 1?
2. Did I pick a **voice register** explicitly, and are my headlines / labels consistent with it?
3. Is my chosen mode NOT in the last 3 /craft outputs in the library?
4. Did I avoid the 15+3 anti-slop signatures?
5. Does my color palette have ≤ 2 hues, all pre-declared in `:root`?
6. Are there ≤ 6 distinct font sizes, all referencing a scale?
7. Does the structural motif match what a designer at the **canonical reference** (Step 1) would do?
8. Did I embed all 5 `<meta name="artifold:*">` tags?
9. Could a designer point at ONE distinctive choice and say "that's intentional"?
10. Could someone read just the headlines and immediately know which voice register I picked?

If any fail, iterate.

---

## Step 7: Save to the canonical inbox

If `artifold` is installed:
- Run `artifold inbox <topic>` via Bash to get the canonical path
- Use the Write tool to save the artifact to that exact path
- Tell the user the path you wrote + the mode + register you picked

If Artifold isn't installed:
- Default to `~/artifold-inbox/YYYY-MM-DD-<topic-slug>.html`

After saving:
- Tell the user the path you wrote to (one line)
- Tell them: *"Will show up in your Artifold dashboard within ~2 seconds. Picked `<mode>` mode in `<register>` voice."*
- Don't dump the HTML in chat — the file is the deliverable.

## Naming convention examples

- `2026-05-26-30-day-strength-tracker.html`
- `2026-05-26-sf-apartment-comparison.html`
- `2026-05-26-poker-probability-explainer.html`

Slugs are short (4–6 words), lowercase, kebab-case, no special chars.

---

## A note on voice

You're writing for a thoughtful user. Don't pad explanations, don't apologize for design choices, don't enumerate "I'll create three sections with..." before writing them. Show the artifact, briefly note the one or two key design decisions (mode + register + why), and stop.
