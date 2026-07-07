# Fonts — never ship the bare system stack

System-font-only output is the single fastest "this is cheap/AI" tell. One `<link>` fixes it. **Inter-as-the-only-font is now itself a slop signature** — it's fine as a body workhorse but vary the display face and pick intentionally.

Rules:
- Load via Google Fonts `<link>` in `<head>` with `display=swap` and a **complete fallback chain ending in `system-ui`**. (For true offline self-containment, base64 a WOFF2 instead — only when the file must work with no network.)
- Prefer **variable fonts** (one URL, all weights + optical sizes).
- Pair a **distinctive display/heading face** with a **calm, readable body face**. Don't use the display face for body.
- Tighten large display (`letter-spacing:-0.02em`); add tracking to ALL-CAPS labels (`letter-spacing:.06–.1em`).

## Pairings by mood → mode family

| Mood / family | Heading | Body | `<link>` href (after the two preconnects) |
|---|---|---|---|
| Editorial / literary (A) | **Fraunces** (opsz) | Inter | `family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;700` |
| High-end literary (A) | **Cormorant Garamond** | Karla | `family=Cormorant+Garamond:wght@500;600;700&family=Karla:wght@400;500;700` |
| Magazine / fashion (F) | **Playfair Display** | Source Serif 4 | `family=Playfair+Display:wght@600;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600` |
| Magazine alt (F) | **Libre Baskerville** | DM Sans | `family=Libre+Baskerville:wght@400;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700` |
| Warm long-read | **Fraunces** | Lora | `family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Lora:wght@400;500;600` |
| Document-pro / serious (B) | **Newsreader** | Inter | `family=Newsreader:opsz,wght@6..72,400;6..72,600&family=Inter:wght@400;500;600` |
| Document-pro alt (B) | **IBM Plex Serif** | IBM Plex Sans | `family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600` |
| Quirky / tech | **Bricolage Grotesque** | Inter | `family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Inter:wght@400;500;700` |
| Geometric / playful (D) | **Syne** | Plus Jakarta Sans | `family=Syne:wght@600;800&family=Plus+Jakarta+Sans:wght@400;500;700` |
| Crafted detail | **Instrument Serif** | Work Sans | `family=Instrument+Serif:ital@0;1&family=Work+Sans:wght@400;500;600` |
| Expressive / poster (C) | **Anton** (or Archivo 900) | Inter | `family=Anton&family=Inter:wght@400;500;700` |
| Expressive alt (C) | **Syne** (800) | Space Grotesk | `family=Syne:wght@700;800&family=Space+Grotesk:wght@400;500;700` |
| Data-dashboard (A) | **Inter Tight** | JetBrains Mono *(numerals)* | `family=Inter+Tight:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700` |
| Terminal / mono (F) | **JetBrains Mono** | Space Mono | `family=JetBrains+Mono:wght@400;700&family=Space+Mono:wght@400;700` |
| Boarding-pass / ticket (D) | Space Grotesk | **JetBrains Mono** *(fields)* | `family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;500;700` |
| Handwritten-journal | **Caveat** (or Shantell Sans) | Inter | `family=Caveat:wght@500;700&family=Inter:wght@400;500` |
| Typewriter / dossier / ship's log (G) | **Special Elite** | Lora | `family=Special+Elite&family=Lora:wght@400;500;600` |
| Warm hand / kids / café (H) | **Shantell Sans** | Nunito | `family=Shantell+Sans:wght@500;700&family=Nunito:wght@400;600;700` |
| True handwriting (H, display only) | **Homemade Apple** | Lora | `family=Homemade+Apple&family=Lora:wght@400;500` |
| Pixel / arcade (G, display ≥18px only) | **Press Start 2P** | Space Grotesk | `family=Press+Start+2P&family=Space+Grotesk:wght@400;500;700` |
| Retro terminal / teletext (G) | **VT323** | Space Mono | `family=VT323&family=Space+Mono:wght@400;700` |
| Wes-Anderson symmetric (H) | **Jost** | Karla | `family=Jost:wght@500;600;700&family=Karla:wght@400;500;700` |
| Gentle pastoral (H) | **Fraunces** (soft axis) | Nunito | `family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Nunito:wght@400;600` |

## Copy-paste head block
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?<HREF-FROM-TABLE>&display=swap" rel="stylesheet">
```
```css
:root{
  --font-head:"Fraunces", Georgia, "Times New Roman", serif;       /* swap per pairing */
  --font-body:"Inter", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-mono:"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
```

## Notes
- Optical-size axis (`opsz`) on Fraunces / Newsreader / Source Serif 4 / Bricolage = use large for display, small for body — automatically "designed."
- Restrained modes: cap display weight (e.g. 500–700, never 800+ for body). Expressive modes: go heavy (Anton, Archivo 900) for the giant-typographic-figure device.
- **Handwriting fonts are seasoning, not the meal:** Caveat / Homemade Apple / Shantell Sans for headings, margin notes, and annotations only — never paragraphs of body text. Pixel fonts (Press Start 2P, VT323) never below 18px and never for body.
- Don't load more than **two families** (a third only for a mono numeral/field role). More = slow + incoherent.
- Rotate the pairing like every other axis — don't reach for Fraunces/Inter every time just because it's first in the table.
