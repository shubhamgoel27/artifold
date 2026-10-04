# Design Modes: the skin (fonts · color · texture)

Mode controls *paint only*, typefaces, palette, texture, ornament, never page architecture. A mode renders under many skeletons. Fit first; freshness breaks ties (SKILL.md section 4).

**Each mode now has a real exemplar + a concrete hex triad** so it's a *target*, not an adjective. The triad is `bg · ink · accent`, a **starting point to adapt and expand into a full ramp** (see `references/craft-recipes.md`), not an official brand value. Honor each family's restraint budget. Font column = a pairing from `references/fonts.md`.

> **Use the exemplar.** "swiss-grid" is vague; "render like Linear, `#5E6AD2` on near-black, Inter Tight, 8px grid" is not. Picture the exemplar's actual product/page before writing CSS.

---

## Family A: Restrained / editorial · *budget: ≤2 hues, ≤6 sizes, color = meaning*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `editorial-newsprint` | NYT Opinion / *n+1* | `#faf8f3 · #1a1a1a · #9b2226` | Newsreader / Inter | essays, wine lists, slow-news |
| `swiss-grid` | Linear / Vercel | `#ffffff · #08090a · #5e6ad2` | Inter Tight / Inter | architectural, museum, design |
| `corporate-memo` | Stripe / McKinsey | `#ffffff · #0a2540 · #635bff` | IBM Plex Sans / Inter | decision docs, post-mortems |
| `museum-label` | MoMA wall text / Phaidon | `#f6f4ef · #1c1c1c · #8c1d18` | Cormorant Garamond / Karla | single-object focus, curation |
| `technical-blueprint` | Distill.pub / Observable | `#f3f0e7 · #0d2b45 · #0a7e9e` | Newsreader / JetBrains Mono | ML/math/CS explainers, specs |
| `data-dashboard` | Grafana / Vercel Analytics | `#0b0d12 · #e6e6e6 · #11d1a3` (+signal `#f0506b`) | Inter Tight / JetBrains Mono | KPI views, monitoring |

## Family B: Document-pro · *budget: ≤2 hues + 1 stamp/spot, dense, serious*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `dossier-casefile` | CIA/FBI declassified file | `#cdb892 · #241c12 · #9e2b25` | JetBrains Mono / Space Grotesk | investigations, "everything on X" |
| `almanac` | Old Farmer's Almanac / Whole Earth Catalog | `#f3ecd8 · #2a2418 · #5a4a1f` | IBM Plex Serif / IBM Plex Sans | facts, rankings, yearly summaries |
| `scientific-poster` | NeurIPS / IEEE poster | `#ffffff · #1a2b4a · #b5121b` | IBM Plex Sans / IBM Plex Serif | research summaries, methods |
| `legal-brief` | SCOTUS slip opinion / Bloomberg Law | `#fdfdf9 · #1a1a1a · #6b1f2a` | Newsreader / Inter | terms, formal analyses |
| `annual-report` | Apple / Pentagram report | `#ffffff · #111111 · #0071e3` | Inter Tight / Source Serif 4 | year-in-review, org summaries |
| `patent-filing` | USPTO drawing / Dieter Rams | `#ffffff · #111111 · #1b4f8a` | IBM Plex Mono / IBM Plex Sans | how-it-works, invention framing |

## Family C: Expressive-graphic · *budget: full palettes, dramatic size jumps, color may delight*

| Mode | Exemplar | Triad `bg · ink · accents` | Fonts | Good for |
|---|---|---|---|---|
| `poster-maximalist` | Pentagram / Wieden+Kennedy | `#f3e9d6 · #141008 · #ff3b1f #1b35d6 #ffc400` | Anton / Inter | announcements, single statements |
| `risograph-print` | Risotto Studio / Hato Press | `#f7f3e8 · #111 · #0033cc #ff6600 #ff48b0` | Bricolage Grotesque / Inter | zines, event bills, indie posters |
| `synthwave-grid` | Outrun / *Kung Fury* | `#0d0221 · #f6e9ff · #ff2e97 #05d9e8` | Syne / Space Grotesk | retro tech, game-y, energetic |
| `album-sleeve` | Blue Note / 4AD / Hipgnosis | `#1a1a1a · #f3efe6 · #e8b800 #d23c2c` | Syne / Plus Jakarta Sans | rankings, "greatest hits" |
| `protest-broadside` | Shepard Fairey / Barbara Kruger | `#f2ead8 · #111 · #d7261e` (Kruger: `#e3001b·#fff·#000`) | Anton / Work Sans | calls to action, strong opinions |
| `infographic-pop` | Information is Beautiful / Nigel Holmes | `#fffdf7 · #16242e · #2ec4b6 #ff9f1c #e71d36` | Plus Jakarta Sans / Inter | stats for general audiences |

## Family D: Playful-tactile · *budget: 3–4 hues, object-like; pairs with single-object / grid-of-tiles*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `trading-card` | Pokémon / Panini / MTG | `#1b2a4a · #f4f1e8 · #f4c542` (rarity `#c0392b`) | Plus Jakarta Sans / Inter | profiles, comparisons, "the set" |
| `boarding-pass` | airline BP / Apple Wallet pass | `#ffffff · #13202b · #0a7d5a` | Space Grotesk / JetBrains Mono | itineraries, schedules, steps |
| `recipe-card` | Betty Crocker card / NYT Cooking | `#f7f1e3 · #2a2118 · #7a1f1f` | Caveat / Work Sans | procedures, how-tos, kits |
| `scrapbook-collage` | Tumblr / Sister Corita / cut-paper zine | `#efe7d6 · #1a1a1a · #e8d44d #d23c2c #4a90d9` | Caveat / DM Sans | personal recaps, trips, mood |
| `comic-panel` | Marvel/DC / Chris Ware | `#fffef5 · #111 · #ff4136 #2c6e9b` | Bricolage Grotesque / Inter | narratives, before/after, steps |
| `board-game-box` | Ticket to Ride / Catan | `#1d3a2a · #f5ecd6 · #d4a017` | Syne / Plus Jakarta Sans | systems, game-like processes |

## Family E: Spatial-diagrammatic · *budget: 2–6 line/band colors, layout-as-content; pairs with radial / split-screen*

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `transit-map` | London Tube (Beck) / NYC MTA | `#ffffff · #1c1c1c · line set #e32017 #0098d4 #00782a #f3a9bb` | Inter / Inter | roadmaps, processes, networks |
| `cad-exploded` | IKEA instructions / Haynes manual | `#ffffff · #111 · #1b4f8a` (line-art b&w) | IBM Plex Mono / IBM Plex Sans | assembly, component breakdowns |
| `gallery-wall` | Tate / Gagosian salon hang | `#ece9e2 · #1c1c1c · #6b1f2a` | Cormorant Garamond / Work Sans | collections, portfolios |
| `annotated-schematic` | engineer's notebook / Tufte | `#faf8f2 · #1a1a1a · #d6261f` | Newsreader / JetBrains Mono | teardowns, explainers over a figure |
| `sankey-flow` | NYT flow viz / financial Sankey | `#ffffff · #16242e · bands #4e79a7 #f28e2b #59a14f` | Inter Tight / Inter | budgets, conversions, where-it-goes |
| `periodic-table` | Mendeleev wall chart | `#f4f1e8 · #1c1c1c · category fills #7fb8a4 #e8a87c #a4c2e8` | Inter Tight / JetBrains Mono | element-grids of anything, taxonomies with properties |
| `topographic-map` | USGS quad / Swiss hiking map | `#f2efe4 · #4a3f2f · contour #b08d57 water #7ba7bc` | Jost / Karla | terrain of a topic, difficulty gradients, expeditions |

## Family F: Web-native / nostalgic · *budget varies per mode (noted)*

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

## Family G: Diegetic worlds · *the page IS an object from another world; commit fully to the fiction, budget = whatever the world dictates*

These modes only work with total commitment (SKILL.md section 4, the conceit). Pair with a matching conceit and let the world dictate every token.

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
| `airline-safety-card` | laminated seat-pocket card | `#f7f7f2 · #1d3557 · #e63946 #f4a261` (flat pictograms, no prose) | Jost / Inter | procedures, do/don't pairs, emergency plans |
| `pulp-paperback` | 1950s dime-store cover | `#e8d5a3 · #241c12 · #c1121f #f4a300` (worn edges, lurid type) | Anton / Lora | dramatic retellings, postmortems as noir |
| `vhs-rental` | Blockbuster shelf / VHS sleeve | `#10131a · #f2e9d8 · #ffcc00 #2364aa` | Syne / Inter | retrospectives, "now showing" lists, media |
| `racing-form` | betting slip / turf-club program | `#f5efdc · #1d241d · #0f6c3c #b8860b` | IBM Plex Mono / IBM Plex Sans | odds, predictions, head-to-heads |
| `heist-blueprint` | Ocean's-Eleven planning wall | `#0e2a47 · #dce8f2 · #f2c14e` (white-line plans on midnight) | Space Grotesk / JetBrains Mono | multi-phase plans, risk maps, "the crew" |

## Family H: Warm & personal · *budget: 3–4 warm hues, soft edges, at least one handmade touch; must feel addressed to ONE person*

The anti-corporate family. If Family A is a designer's portfolio, Family H is a letter on the kitchen table. These pair naturally with the warmth rules in SKILL.md section 7 (asides, P.S., colophon).

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

## Family I: Movements & eras · *budget: whatever the movement actually practiced; get the era's grid and ornament right or don't pick it*

Each of these is a real design movement with real rules. Half-committing produces costume, not design, study the exemplar's actual composition (Bauhaus means asymmetric geometry and primaries, not "red circle somewhere").

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `bauhaus-1923` | Dessau posters / Moholy-Nagy | `#f2e8d5 · #1a1a1a · #d02e26 #1b4f8a #e8a800` (geometry does the work) | Archivo / Inter | principles, curricula, anything modular |
| `art-deco-metropolis` | Gatsby invitation / Chrysler lobby | `#101820 · #e8d7b0 · #c9a227` (gold on midnight, sunburst frames) | Limelight / Jost | galas, launches, glamorous best-ofs |
| `constructivist-agitprop` | Rodchenko / El Lissitzky | `#e8dfc8 · #1a1a1a · #d02e26` (hard diagonals, photomontage) | Oswald / Inter | rallying cries, bold announcements |
| `mid-century-jetset` | PanAm & TWA travel posters | `#f4ead2 · #22333b · #2364aa #e0803d` (flat shapes, optimism) | Jost / DM Sans | itineraries, destination guides |
| `memphis-milano` | Sottsass / 1981 Memphis group | `#fdf6ec · #1a1a1a · #f45b69 #17bebb #ffc914` (squiggles, terrazzo) | Baloo 2 / Nunito | playful inventories, creative recaps |
| `medieval-illuminated` | Book of Kells / illuminated MS | `#f3e9d0 · #2b1d0e · #8b1e3f #c9a227 #1b4f8a` (gold leaf, drop caps, borders) | UnifrakturMaguntia *(display only, ≥24px)* / EB Garamond | epics, sagas, mock-heroic anything |
| `ukiyo-e-woodblock` | Hokusai / Hiroshige | `#ece5d3 · #2b3a42 · #4a7ba6 #c1614a` (flat planes, wave lines, seal stamp) | Zen Antique / Karla | nature, journeys, seasonal guides |
| `frutiger-aero-y2k` | 2004 Windows XP / Nokia ads | `#eaf4fb · #1b3a4b · #35a7ff #7ed957` (gloss, bubbles, sky) | Exo 2 / Inter | tech nostalgia, optimism, product pages |

## Family J: Desi & diasporic · *budget: the source object's own maximalism or formality; ornament is structural here, not decoration*

This family exists because this library belongs to one household (the general rule: build modes from the reader's own culture, these are Shubham and Annu's). Use for content with any personal, familial, or celebratory register; never as exotic paint on unrelated corporate content.

| Mode | Exemplar | Triad `bg · ink · accent` | Fonts | Good for |
|---|---|---|---|---|
| `bollywood-hand-painted` | 1970s hand-painted film posters | `#f2d8a7 · #2b1a12 · #d02e26 #f4a300 #1b7ca6` (brushy, melodramatic) | Yatra One / Baloo 2 | dramatic recaps, sagas, hype pages |
| `shaadi-invite` | Indian wedding card, gold on maroon | `#5c1a1a · #f3e2c0 · #c9a227` (foil borders, formal blessings) | Cinzel / EB Garamond | celebrations, announcements, milestones |
| `jingle-truck` | South-Asian truck art | `#1b7ca6 · #fdf6ec · #d02e26 #f4a300 #2e8b57` (ornate borders on everything) | Baloo 2 / Nunito | maximalist joy, lists with blessings, horns-ok energy |
| `cricket-scorecard` | Test-match scorecard / Wisden | `#f5f0e0 · #1d241d · #0f6c3c #b8860b` (innings tables, extras, fall of wickets) | IBM Plex Mono / IBM Plex Sans | stats-of-anything, innings-style recaps, partnerships |

---

## The mode forge: when the subject brings its own world

If the subject owns a real, strong visual language, a club's kit and crest, a city's transit signage, a game's UI, a brand, a specific decade of a specific place, don't pick a catalog mode: **forge one from the subject's actual world.** Pull the real palette (verified from primary sources, not memory), the nearest Google Font to its typographic feel, and the furniture that world would actually print (a matchday programme prints lineups; a metro prints strip maps).

Then **append the forged mode to this file**, one table row in the closest family, or under a `## Forged` heading, with exemplar, triad, fonts, and good-for, so the catalog grows a new permanent entry every time a strong subject passes through. A library that forges is never finished, which is the point.

Rules: CSS/SVG homage, never hotlinked copyrighted art · palette/logo facts verified against the real thing · a forged mode still declares and obeys a restraint-or-maximalism budget · forge only when the world is genuinely strong (a generic SaaS product does not have a world; Arsenal does).

## The remix operator: manufacture novel combinations

Axis rotation prevents repeats; remixing manufactures *fresh* looks. Formula:

> **[Exemplar A's structural property] + [Exemplar B's palette or type] + supporting tokens = emotional outcome**

Take the grid/structure from one exemplar and the color/type from another in a *different family*. Examples:
- `Linear's 8px grid + Blue Note's #e8b800/#d23c2c + a serif display` → confident, warm-but-precise.
- `IKEA instruction line-art + Risograph spot inks` → friendly technical.
- `SCOTUS slip-opinion numbering + Information-is-Beautiful brights` → playful-authoritative.
- `Tube-map lines + Moleskine lined paper` → hand-planned roadmap.

When to remix: the topic is generic, the obvious mode is on cooldown, or you want the "one non-obvious pairing" the skill rewards. State the remix in one line (and in the `design-mode` meta tag as `A×B`).

## Picking a mode
1. **Format/topic → family.** Serious analysis → A/B · statement/announcement → C · personal/fun/kit → D · network/teardown/flow → E · nostalgic/playful-web → F · strong conceit ("the page IS a thing") → G · made-for-one-person, warm → H · era/movement energy ("make it 1923 / 1969 / 2004") → I · personal-cultural, celebratory → J. **When torn between a professional family and G/H/I/J at `read`/`experience` tier, lean away from professional**, the corporate look is never under-represented in the library. At **`glance` tier, lean A/B** and let flawless execution be the signature: a Vignelli-quiet reference card beats a themed one you have to decode while cooking.
2. **Freshness breaks ties** (SKILL.md section 4); rotate exemplars too (don't always reach for Linear/Stripe).
3. **Picture the exemplar, then build the triad into a full ramp** via `craft-recipes.md` §5. Honor the family's restraint budget.
