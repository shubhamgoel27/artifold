# Design Modes — the skin (fonts · color · texture)

Mode controls *paint only* — typefaces, palette, texture, ornament — not page architecture (that's the Layout Archetype). A mode renders under many skeletons. Rotate: don't reuse a mode from the last 3 outputs, and don't repeat the `(layout × mode)` pair from the last 5.

**Each mode now has a real exemplar + a concrete hex triad** so it's a *target*, not an adjective. The triad is `bg · ink · accent` — a **starting point to adapt and expand into a full ramp** (see `references/craft-recipes.md`), not an official brand value. Honor each family's restraint budget. Font column = a pairing from `references/fonts.md`.

> **Use the exemplar.** "swiss-grid" is vague; "render like Linear — `#5E6AD2` on near-black, Inter Tight, 8px grid" is not. Picture the exemplar's actual product/page before writing CSS.

---

## Family A — Restrained / editorial · *budget: ≤2 hues, ≤6 sizes, color = meaning*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `editorial-newsprint` | NYT Opinion / *n+1* | `#faf8f3 · #1a1a1a · #9b2226` | Newsreader / Inter | essays, wine lists, slow-news |
| `swiss-grid` | Linear / Vercel | `#ffffff · #08090a · #5e6ad2` | Inter Tight / Inter | architectural, museum, design |
| `corporate-memo` | Stripe / McKinsey | `#ffffff · #0a2540 · #635bff` | IBM Plex Sans / Inter | decision docs, post-mortems |
| `museum-label` | MoMA wall text / Phaidon | `#f6f4ef · #1c1c1c · #8c1d18` | Cormorant Garamond / Karla | single-object focus, curation |
| `technical-blueprint` | Distill.pub / Observable | `#f3f0e7 · #0d2b45 · #0a7e9e` | Newsreader / JetBrains Mono | ML/math/CS explainers, specs |
| `data-dashboard` | Grafana / Vercel Analytics | `#0b0d12 · #e6e6e6 · #11d1a3` (+signal `#f0506b`) | Inter Tight / JetBrains Mono | KPI views, monitoring |

## Family B — Document-pro · *budget: ≤2 hues + 1 stamp/spot, dense, serious*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `dossier-casefile` | CIA/FBI declassified file | `#cdb892 · #241c12 · #9e2b25` | JetBrains Mono / Space Grotesk | investigations, "everything on X" |
| `almanac` | Old Farmer's Almanac / Whole Earth Catalog | `#f3ecd8 · #2a2418 · #5a4a1f` | IBM Plex Serif / IBM Plex Sans | facts, rankings, yearly summaries |
| `scientific-poster` | NeurIPS / IEEE poster | `#ffffff · #1a2b4a · #b5121b` | IBM Plex Sans / IBM Plex Serif | research summaries, methods |
| `legal-brief` | SCOTUS slip opinion / Bloomberg Law | `#fdfdf9 · #1a1a1a · #6b1f2a` | Newsreader / Inter | terms, formal analyses |
| `annual-report` | Apple / Pentagram report | `#ffffff · #111111 · #0071e3` | Inter Tight / Source Serif 4 | year-in-review, org summaries |
| `patent-filing` | USPTO drawing / Dieter Rams | `#ffffff · #111111 · #1b4f8a` | IBM Plex Mono / IBM Plex Sans | how-it-works, invention framing |

## Family C — Expressive-graphic · *budget: full palettes, dramatic size jumps, color may delight*

| Mode | Exemplar | Triad `bg · ink · accents` | Fonts | Good for |
|---|---|---|---|---|
| `poster-maximalist` | Pentagram / Wieden+Kennedy | `#f3e9d6 · #141008 · #ff3b1f #1b35d6 #ffc400` | Anton / Inter | announcements, single statements |
| `risograph-print` | Risotto Studio / Hato Press | `#f7f3e8 · #111 · #0033cc #ff6600 #ff48b0` | Bricolage Grotesque / Inter | zines, event bills, indie posters |
| `synthwave-grid` | Outrun / *Kung Fury* | `#0d0221 · #f6e9ff · #ff2e97 #05d9e8` | Syne / Space Grotesk | retro tech, game-y, energetic |
| `album-sleeve` | Blue Note / 4AD / Hipgnosis | `#1a1a1a · #f3efe6 · #e8b800 #d23c2c` | Syne / Plus Jakarta Sans | rankings, "greatest hits" |
| `protest-broadside` | Shepard Fairey / Barbara Kruger | `#f2ead8 · #111 · #d7261e` (Kruger: `#e3001b·#fff·#000`) | Anton / Work Sans | calls to action, strong opinions |
| `infographic-pop` | Information is Beautiful / Nigel Holmes | `#fffdf7 · #16242e · #2ec4b6 #ff9f1c #e71d36` | Plus Jakarta Sans / Inter | stats for general audiences |

## Family D — Playful-tactile · *budget: 3–4 hues, object-like; pairs with single-object / grid-of-tiles*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `trading-card` | Pokémon / Panini / MTG | `#1b2a4a · #f4f1e8 · #f4c542` (rarity `#c0392b`) | Plus Jakarta Sans / Inter | profiles, comparisons, "the set" |
| `boarding-pass` | airline BP / Apple Wallet pass | `#ffffff · #13202b · #0a7d5a` | Space Grotesk / JetBrains Mono | itineraries, schedules, steps |
| `recipe-card` | Betty Crocker card / NYT Cooking | `#f7f1e3 · #2a2118 · #7a1f1f` | Caveat / Work Sans | procedures, how-tos, kits |
| `scrapbook-collage` | Tumblr / Sister Corita / cut-paper zine | `#efe7d6 · #1a1a1a · #e8d44d #d23c2c #4a90d9` | Caveat / DM Sans | personal recaps, trips, mood |
| `comic-panel` | Marvel/DC / Chris Ware | `#fffef5 · #111 · #ff4136 #2c6e9b` | Bricolage Grotesque / Inter | narratives, before/after, steps |
| `board-game-box` | Ticket to Ride / Catan | `#1d3a2a · #f5ecd6 · #d4a017` | Syne / Plus Jakarta Sans | systems, game-like processes |

## Family E — Spatial-diagrammatic · *budget: 2–6 line/band colors, layout-as-content; pairs with radial / split-screen*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `transit-map` | London Tube (Beck) / NYC MTA | `#ffffff · #1c1c1c · line set #e32017 #0098d4 #00782a #f3a9bb` | Inter / Inter | roadmaps, processes, networks |
| `cad-exploded` | IKEA instructions / Haynes manual | `#ffffff · #111 · #1b4f8a` (line-art b&w) | IBM Plex Mono / IBM Plex Sans | assembly, component breakdowns |
| `gallery-wall` | Tate / Gagosian salon hang | `#ece9e2 · #1c1c1c · #6b1f2a` | Cormorant Garamond / Work Sans | collections, portfolios |
| `annotated-schematic` | engineer's notebook / Tufte | `#faf8f2 · #1a1a1a · #d6261f` | Newsreader / JetBrains Mono | teardowns, explainers over a figure |
| `sankey-flow` | NYT flow viz / financial Sankey | `#ffffff · #16242e · bands #4e79a7 #f28e2b #59a14f` | Inter Tight / Inter | budgets, conversions, where-it-goes |

## Family F — Web-native / nostalgic · *budget varies per mode (noted)*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `brutalist-web` | Gumroad / Bloomberg Businessweek | `#ffffff · #000000 · #ff90e8` (raw borders OK) | Space Grotesk / Inter | anti-design, indie, rebellious |
| `terminal-tui` | cool-retro-term / htop / Vim | `#0c0c0c · #33ff66 · #ffb000` (phosphor) | JetBrains Mono / Space Mono | dev tools, logs, status |
| `retro-90s-web` | GeoCities / Space Jam site | `#c0c0c0 · #000080 · #ff0000` (tiled bg) | Times / system | nostalgic, fan pages, games |
| `field-guide` | Sibley / Audubon / Nat Geo | `#f5f1e6 · #2c2c22 · #6b8e5a #a6611a` | Fraunces / Lora | nature guides, taxonomies |
| `magazine-fashion` | Vogue / Harper's Bazaar / Kinfolk | `#fbf7f2 · #1a1714 · #d2042d` | Playfair Display / Source Serif 4 | tier lists, "best of", rankings |
| `softpop-pastel` | Duolingo / Headspace | `#fff9f0 · #3a2e22 · #58cc02 #ffc83d #ff9600` | Plus Jakarta Sans / Inter | family-facing, kids, lifestyle |
| `monochrome-poster` | Massimo Vignelli screenprint | `#f2efe6 · #111 · #e3001b` (one hue + black) | Anton / Inter | posters, single statements |
| `handwritten-journal` | Moleskine / Field Notes / bullet journal | `#fbfaf5 · #1d3a8a · #c0392b` (lined bg) | Caveat / Inter | logs, recipes, casual notes |
| `zine-photocopy` | punk flyer / Xerox zine | `#ededed · #111 · #ff2e63` (high-contrast b&w + 1 spot) | Bricolage Grotesque / Space Mono | personal essays, music, scenes |

## Family G — Diegetic worlds · *the page IS an object from another world; commit fully to the fiction, budget = whatever the world dictates*

These modes only work with total commitment. A tarot spread with a corporate footer breaks the spell. Pair with a matching conceit (SKILL.md Step 2·0) and let the world dictate every token.

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `tarot-spread` | Rider-Waite deck / Pamela Colman Smith | `#14101e · #ecdfc8 · #c9a227` | Cormorant Garamond / Karla | decisions, options, "what the future holds" |
| `detective-corkboard` | evidence wall / Pepe Silvia | cork `#8a6a48 · paper #f4efe4 · string #d22c2c` | Special Elite / Inter | investigations, connecting dots, debugging |
| `mixtape-liner` | cassette J-card / 90s mixtape | `#f2e8d5 · #1c1a17 · #e2543e` | Caveat / Space Mono | rankings, playlists, "songs about X" |
| `departures-board` | Solari split-flap / airport hall | `#101214 · #e8e6e0 · #f5d90a` (amber flaps) | JetBrains Mono / Inter | schedules, statuses, what's-next |
| `mission-control` | Apollo consoles / NASA 1969 | `#0a0e12 · #9fd8cb · #f0a02f` | IBM Plex Mono / IBM Plex Sans | launches, milestones, go/no-go checklists |
| `teletext-ceefax` | BBC Ceefax / Minitel | `#000000 · #ffffff · #ffff00 #00ffff` (blocky) | VT323 / Space Mono | news-y, scores, retro-info fun |
| `cereal-box` | vintage Kellogg's / Saturday-morning shelf | `#f7c948 · #1d3557 · #e63946` | Anton / Plus Jakarta Sans | "now with X!", features, kid-energy topics |
| `seed-packet` | vintage Burpee packets | `#f5eed8 · #2f3b2a · #c26a34` | Fraunces / Lora | plans that grow, habits, gardens of anything |
| `playbill-theater` | Broadway Playbill / vintage program | `#f9f4e6 · #191919 · #c9a227` | Playfair Display / Source Serif 4 | casts of characters, acts, events |
| `arcade-cabinet` | 80s marquee / pixel art | `#0d0630 · #ffffff · #ff2975 #00e5ff #ffd319` | Press Start 2P *(display only, ≥18px)* / Space Grotesk | games, scores, levels, challenges |
| `ships-log` | expedition journal / Shackleton | `#efe6d2 · #26221b · #1b4f72` | Special Elite / Lora | journeys, day-by-day accounts, weathering |
| `cabinet-of-curiosities` | Victorian wunderkammer / Verne | `#221a14 · #e8dcc4 · #b08d3e #7c9a63` | Cormorant Garamond / Work Sans | collections, oddities, specimen catalogs |

## Family H — Warm & personal · *budget: 3–4 warm hues, soft edges, at least one handmade touch; must feel addressed to ONE person*

The anti-corporate family. If Family A is a designer's portfolio, Family H is a letter on the kitchen table. These pair naturally with the warmth rules in SKILL.md Step 3.5 (asides, P.S., colophon).

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `amelie-whimsy` | *Amélie* / Montmartre café at night | `#1f6f5c · #f3e2c0 · #b3352c #c9a227` | Cormorant Garamond / Karla | small pleasures, guides with a wink, city love |
| `wes-anderson` | *Grand Budapest Hotel* | `#f2d5cb · #4a3b2f · #a4243b #2e5e4e` | Archivo / Futura-adjacent (Jost) | symmetric inventories, chapters, capers |
| `ghibli-pastoral` | Totoro countryside / Kiki's bakery | `#f3f7e9 · #3a4a3f · #7fb069 #f4a259` | Fraunces / Nunito | gentle guides, nature, slow living |
| `grandmas-cookbook` | 1970s stained recipe cards | `#f8f1e0 · #4a3728 · #b5533c` | Caveat / Lora | recipes, traditions, inherited wisdom |
| `kids-picture-book` | Eric Carle / Oliver Jeffers | `#fffdf4 · #2b2b2b · #e63946 #f4a261 #2a9d8f` | Shantell Sans / Nunito | explain-like-I'm-five, big shapes, joy |
| `indie-cafe-menu` | third-wave kraft menu / chalkboard | `#d9c7a7 · #33291c · #d98e4a` | Shantell Sans / Work Sans | menus of anything, daily specials, picks |
| `postcard-from` | vintage travel postcard + airmail edge | `#f4ead6 · #23405c · #c0392b` (airmail stripes) | Playfair Display / Karla | trips, wish-you-were-here recaps, places |
| `letter-from-a-friend` | stationery + real handwriting | `#fffdf7 · #2b3a67 · #c0392b` | Homemade Apple *(sparingly)* / Lora | advice, recaps, anything personal |

---

## The remix operator — manufacture novel combinations

Axis rotation prevents repeats; remixing manufactures *fresh* looks. Formula:

> **[Exemplar A's structural property] + [Exemplar B's palette or type] + supporting tokens = emotional outcome**

Take the grid/structure from one exemplar and the color/type from another in a *different family*. Examples:
- `Linear's 8px grid + Blue Note's #e8b800/#d23c2c + a serif display` → confident, warm-but-precise.
- `IKEA instruction line-art + Risograph spot inks` → friendly technical.
- `SCOTUS slip-opinion numbering + Information-is-Beautiful brights` → playful-authoritative.
- `Tube-map lines + Moleskine lined paper` → hand-planned roadmap.

When to remix: the topic is generic, the obvious mode is on cooldown, or you want the "one non-obvious pairing" the skill rewards. State the remix in one line (and in the `design-mode` meta tag as `A×B`).

## Picking a mode
1. **Format/topic → family.** Serious analysis → A/B · statement/announcement → C · personal/fun/kit → D · network/teardown/flow → E · nostalgic/playful-web → F · strong conceit ("the page IS a thing") → G · made-for-one-person, warm → H. **When torn between a professional family and G/H at `read`/`experience` tier, lean G/H** — the corporate look is never under-represented in the library. At **`glance` tier, lean A/B** and let flawless execution be the signature: a Vignelli-quiet reference card beats a themed one you have to decode while cooking.
2. **Rotate** off the last 3 modes; don't repeat the last 5 `(layout × mode)` pairs; rotate exemplars too (don't always reach for Linear/Stripe).
3. **Picture the exemplar, then build the triad into a full ramp** via `craft-recipes.md` (60/30/10 dominance, never pure-black body text). Honor the family's restraint budget.
