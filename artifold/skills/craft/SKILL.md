---
name: craft
description: Use whenever the user asks for a "report", "dashboard", "one-pager", "explainer", "tracker", "guide", "itinerary", or any HTML artifact where the output is a single styled page. Applies opinionated design principles (color/typography/spacing systems) and explicitly avoids the AI-default visual patterns (purple-gradient hero, identical bento cards, decorative emoji, glassmorphism, etc.). If Artifold (the `artifold` CLI) is installed, consults the user's library to inherit a referenced style — or, by default, varies from their past patterns so each new artifact has a distinct identity.
---

# Craft

You are crafting a high-quality HTML artifact. This is **not** generic "make a report" — apply real design discipline and produce something a designer would call intentional.

The default Claude output for these requests is recognizable AI slop: purple-gradient hero, three identical bento cards, decorative emoji on every list item. This skill exists to escape that.

---

## Step 1: Understand the request

Clarify if not obvious:
- **Topic + audience.** "30-day strength tracker for Annu" vs "explainer for a general audience" lead to different choices.
- **Density signal.** Data-dense report? Narrative explainer? Marketing one-pager? Density drives spacing decisions (#10 below).
- **Style reference.** Did the user point to a past artifact ("like dobble", "match my soccer-bulletproof report") or paste an HTML file/URL? That overrides the default variation behavior.
- **Constraint.** Printable, mobile-first, one-page, dark only?

If clear, proceed. Don't over-ask.

---

## Step 2: Style reference (Artifold integration)

Use the Bash tool to check what's available. If the `artifold` command is not installed, skip this step — fall back to pure design-knowledge mode.

**Always use the `--json` flag** when reading from Artifold so the output stays
parseable as the CLI evolves. The stable contract is:
- `artifold designs --json` → array of `{id, name, dir, category, palette[], fonts[], flags{themed,gradient,glass,animated,shadowed}}`
- `artifold designs <id>` → fingerprint object (already JSON, no flag needed)
- `artifold designs <id> --template` → raw CSS + body skeleton (text, not JSON)
- `artifold info <file> --json` → full provenance entry

### A. User explicitly referenced a past artifact
- Run `artifold designs --json` and parse — find the entry whose `name` or
  `dir` best matches what the user mentioned. Confirm with the user if ambiguous.
- Run `artifold designs <id> --template` to load the full CSS + body skeleton.
- Treat that CSS as your baseline. Replace body content for the new topic.
  Keep palette, fonts, tokens, and layout motifs.

### B. User provided an HTML file or URL
- Read the file (or fetch the URL) and extract its `<style>` block + body
  structure manually. Use as style baseline (same as A).

### C. Default — vary from past patterns (anti-slop)
- Run `artifold designs --json` to see the user's library as structured data.
- Aggregate across entries: tally how many are dark-themed, gradient-heavy,
  glass-heavy; tally font families; tally palette dominant hues.
- **Deliberately pick a different direction.** If they've been doing
  dark+gradient, try light+editorial. If they've been doing single-column
  hero, try left-rail or grid. The goal: their library reads as a portfolio
  of distinct artifacts, not 20 variations of the same template.
- Note your variation choice to the user in 1 sentence (*"Your recent
  reports lean dark/glass — going minimal/editorial here for variety."*).

### D. No Artifold, no reference
- Apply design knowledge below from scratch. Pick one strong direction; commit to it.

---

## Step 3: Apply design principles

These are not suggestions — every one was distilled from real sources and meaningfully changes whether the output reads as designed or as auto-generated.

1. **Hierarchy via weight and color, not size.** Cap distinct font sizes at 4–5. Vary `font-weight` (400 + 600/700) and `text-color` (dark primary + mid-grey secondary) first; size last. *(Refactoring UI)*
2. **Start with too much whitespace** (for narrative/marketing artifacts). Section vertical padding ≥ 80px. *(Refactoring UI, Vercel/Geist)*
3. **Define shades up front.** Declare CSS custom properties for your full color ramp (8–10 greys + 5–10 shades of one accent) at the top of `<style>`. Never reach for a new hex mid-build. *(Refactoring UI, free chapter)*
4. **Color carries meaning, or it doesn't appear.** Greyscale by default; accent only on primary action, status, or one data series. Aim: if you deleted every colored pixel, the artifact would still parse. *(Vercel/Geist + Linear)*
5. **Tighten display type.** Any heading ≥ 32px: `letter-spacing: -0.02em; line-height: 1.1`. Body stays default. This single rule is the biggest "looks designed" lever. *(Vercel/Geist)*
6. **Offset shadows, don't blob.** `box-shadow: 0 4px 12px rgba(0,0,0,0.06)` — vertical offset, modest blur. Skip shadows entirely on flat layouts. Never symmetric 40px blurs. *(Refactoring UI)*
7. **Borders are a last resort.** Before adding `border: 1px solid`, try a background-color shift (`grey-50` on white), spacing, or shadow. One border treatment per artifact max. *(Refactoring UI)*
8. **Don't enlarge small icons.** Icons drawn at 16–24px look amateur at 64px. Either keep them native size or skip them. For "feature card" decoration, a small icon in a tinted rounded square is fine — a giant lucide icon centered on a card is the canonical slop signature. *(Refactoring UI)*
9. **Opinionation over flexibility.** One structural motif per artifact. Don't mix "hero with stats + bento grid + side rail + accordion" all on one page. Pick one POV and commit. *(Linear method)*
10. **Density when content earns it.** Information-rich artifacts (dashboards, comparisons, trackers) should be *dense* — 13–14px body, tight rows, lean on tables. Reserve generous whitespace for narrative/marketing. Whitespace-heavy default is itself an AI tell on data-dense content. *(TheAdpharm critique)*
11. **Type scale, not eyeballed sizes.** Use a defined scale (e.g. `12 / 14 / 16 / 20 / 24 / 32 / 48 / 64`). Declare in CSS vars; every `font-size` references one. Hard cap: 6 distinct sizes per artifact. *(Refactoring UI)*
12. **Avoid pure black, avoid grey-on-color.** Body text on white: `#111`–`#1a1a1a`, never `#000`. On a colored panel, text should be a tinted version of that color (or white with reduced opacity) — not mid-grey. *(Refactoring UI)*

---

## Step 4: Anti-slop checklist — avoid these signatures

Before writing CSS, commit to NOT producing these:

1. Purple/indigo-to-violet gradient hero with centered eyebrow + 64px headline + subhead + two CTAs. (The Lovable/v0 default.)
2. Three or four identical bento cards in a row with colored-square icons.
3. Inter as the unexamined default font. If using a sans, justify (Geist, Söhne, IBM Plex) or own Inter with tight tracking.
4. Random emoji decoration. Emojis are punctuation — one per artifact max, ideally zero.
5. Pastel rainbow accents (each section a different pastel).
6. Lucide/Feather icons used decoratively without semantic function.
7. Glassmorphism panels (`backdrop-filter: blur` + 10% white bg). Stale.
8. `rounded-2xl` on everything + medium drop-shadow + border. Shadcn-card-in-triplicate.
9. Identical section rhythm — every section `<h2> + paragraph + 3-col grid`.
10. Hero text in five stacked sizes (eyebrow + headline + subhead + micro + button label). Pick three.
11. Animated gradient blobs / mesh gradients in the background.
12. Centered everything. Real designs use asymmetry; AI defaults center because it's safe.
13. Generic stock-photo placeholders or DALL-E "abstract tech swoosh" hero.
14. Pricing-toggle + 3-tier card + FAQ-accordion triad lifted from SaaS templates.
15. Times-New-Roman fallback when the page reads minimal — declare a real serif or commit to sans.

---

## Step 5: Embed Artifold provenance

In the artifact's `<head>`, include:

```html
<meta name="artifold:intent" content="<10–15 word description of what this artifact accomplishes>">
<meta name="artifold:tool" content="claude">
<meta name="artifold:prompt" content="<the user's original prompt, ≤ 200 chars>">
```

This auto-populates Artifold's library when the file lands in a scanned root. No further work from the user.

If the user referenced a past artifact for style, also add:
```html
<meta name="artifold:style-from" content="<id-of-reference-artifact>">
```

---

## Step 6: Self-check before delivering

Mentally walk through:

1. Palette ≤ 2 hues (one neutral ramp + at most one accent), all shades pre-declared?
2. Accent appears ≤ 3 times, each carrying meaning?
3. ≤ 6 distinct font sizes, all referencing a defined scale?
4. Headings ≥ 32px have negative letter-spacing + tight line-height?
5. Hierarchy driven by weight/color first, size second?
6. Free of decorative emojis (or capped at 1)?
7. Free of decorative icons with no information value?
8. One structural motif, not three layouts competing?
9. Shadows: offset, low opacity, no symmetric blurs?
10. Density matches content type (dense for data, generous for narrative)?
11. Did I avoid the canonical slop combo: centered gradient hero + 3 bento cards + accordion FAQ?
12. Could a designer point at ONE distinctive choice and say "that's intentional"?

If any fail, iterate before delivering.

---

## Step 7: Save to the canonical inbox

**Save the artifact yourself** — don't just hand the user code to copy/paste.

If `artifold` is installed (try `artifold inbox <topic>` via Bash):
- It returns the canonical path, e.g.
  `/Users/me/artifold-inbox/2026-05-26-30-day-strength-tracker.html`
- The path uses today's date (YYYY-MM-DD) prefix + a 4–6 word
  lowercase kebab-case topic slug derived from what the artifact actually is.
- `artifold inbox` also auto-creates the dir and registers it as a watched
  Artifold root, so the artifact gets indexed automatically.
- Use the Write tool to save the artifact to that exact path.

If Artifold isn't installed (command not found):
- Default to `~/artifold-inbox/YYYY-MM-DD-<topic-slug>.html` directly,
  creating the dir if needed.
- Mention to the user: *"Run `pipx install artifold && artifold init` to
  organize these and get a searchable dashboard."*

After saving:
- Tell the user the path you wrote to (one line)
- Tell them: *"It'll show up in your Artifold dashboard within ~2 seconds
  with intent, design fingerprint, and source tagged automatically."*
- Don't dump the HTML in chat — they don't need to scroll through 600
  lines of CSS. The file is the deliverable.

## Naming convention examples

- `2026-05-26-30-day-strength-tracker.html`
- `2026-05-26-sf-apartment-comparison.html`
- `2026-05-26-poker-probability-explainer.html`
- `2026-05-26-eb1a-action-plan.html`

Slugs are short (4–6 words), lowercase, kebab-case, no special chars.

---

## A note on voice

You're writing for a thoughtful user. Don't pad explanations, don't apologize for design choices, don't enumerate "I'll create three sections with..." before writing them. Show the artifact, briefly note the one or two key design decisions you made and why, and stop.
