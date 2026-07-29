# Motion — the animation layer (CSS-first, tier-gated, fail-safe)

Motion is meaning or it's noise. It has exactly four jobs: **orient** (where did this come from), **reveal** (progressive arrival), **connect** (this became that), **delight** (the one weird thing, animated). If an animation isn't doing one of those jobs, cut it.

## The three gates — check all before animating anything

1. **Tier gate (Step 1.5).** `glance`: no JS motion at all (a hover transition is fine). `read`: micro-interactions + at most ONE entrance moment. `experience`: full choreography allowed (GSAP timelines, scroll scenes, Lenis).
2. **Reduced-motion gate.** Every animation sits behind `prefers-reduced-motion` (recipes §8 kill-switch). The static page must read perfectly.
3. **No-JS gate.** The page is COMPLETE with JavaScript disabled. The classic failure: elements authored at `opacity:0` waiting for a reveal that never comes. Use the fail-safe pattern:

```html
<script>document.documentElement.classList.add('js');</script>  <!-- first thing in <head> -->
```
```css
.reveal{ opacity:1; }                       /* base state: visible, always */
.js .reveal{ opacity:0; transform:translateY(14px); }   /* hidden only once JS is confirmed */
```
```js
const motionOK = !matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!motionOK) document.documentElement.classList.remove('js');  // static page, instantly
```

## The ladder — reach for the lightest rung that does the job

1. **CSS transitions/keyframes** (default; covers 80 % of legitimate motion — hovers, marquees, one entrance).
2. **CSS scroll-driven animations** (`animation-timeline: view()`) — scroll reveals with zero JS; degrades to visible content in older browsers.
3. **GSAP via CDN** — only when you need real sequencing (timelines), scroll choreography (ScrollTrigger), or text splitting (SplitText). All plugins are free now.
   ```html
   <script src="https://cdn.jsdelivr.net/npm/gsap@3.13/dist/gsap.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/gsap@3.13/dist/ScrollTrigger.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/gsap@3.13/dist/SplitText.min.js"></script>
   ```
   Usage discipline: `gsap.matchMedia()` for the reduced-motion branch; animate `transform`/`opacity` only; `once:true` on reveals; kill ScrollTriggers you don't need. (For deep GSAP work beyond these patterns, the official agent skills exist: `npx skills add https://github.com/greensock/gsap-skills`.)
4. **Lenis smooth scroll** — `experience`-tier narrative pages ONLY (full-bleed-deck, horizontal-panorama, zigzag story pages). It wraps native scroll so keyboard/anchors/a11y survive, but it still changes how scrolling *feels*, which a utility page must never do.
   ```html
   <script src="https://unpkg.com/lenis@1.3/dist/lenis.min.js"></script>
   ```
   ```js
   if (motionOK) new Lenis({ autoRaf:true });   // never instantiate under reduced-motion
   ```

## The effect palette — vanilla builds of the patterns worth stealing

(Idea sources: react-bits catalog, GSAP showcases. Build them by hand; don't import React.)

| Effect | Job | Build | Min tier | Pairs with |
|---|---|---|---|---|
| split-text rise (words/chars stagger up) | arrival | SplitText, or manual `<span>`-per-word + staggered `animation-delay` | experience | `kinetic-title` |
| count-up stat | emphasize magnitude | ~10-line rAF counter, `tabular-nums`, IntersectionObserver start | read | `hero-dataviz`, giant figure |
| scramble/decrypt text | techy reveal | small rAF character shuffler, settles left→right | experience | `terminal-tui`, `mission-control` |
| typewriter line | narrative pacing | CSS `steps()` + caret blink | read | `ships-log`, `letter-from-a-friend` |
| marquee ticker | ambient status | CSS keyframe translate, duplicated track, pause on hover | read | `ticker-status-row`, `departures-board` |
| spotlight / glare card | tactile hover | CSS custom-prop follows pointer (`--mx`,`--my`), radial-gradient overlay | read | `trading-card`, tile grids |
| magnetic hover | playful precision | tiny lerp toward cursor, snaps back | experience | posters, `arcade-cabinet` |
| parallax layers | depth | CSS scroll-driven or ScrollTrigger; **max 2 layers, subtle** | experience | `full-bleed-deck` |
| pinned scroll-scene | show a transformation | ScrollTrigger pin + scrub; see `scroll-scene` device | experience | papers, product stories |
| aurora / gradient-mesh bg | mood | **CSS only**: 2–3 blurred radial-gradients + grain (§7); no WebGL library | experience | hero areas only, never behind body text |

On WebGL background libraries (vanta.js and kin): **default no.** They cost ~200 KB of three.js to decorate, which is motion-slop economics; the CSS aurora + grain recipe achieves the mood at zero dependencies. The narrow exception: an `experience`-tier artifact whose *conceit is the background* (a fog-world, a night-sky) — and even then, hero-only, `paused` under reduced-motion, never behind running text.

## Motion slop — banned with the same force as Step 4

- **Fade-up-on-every-section** (the AOS look). It's the animated bento grid: uniform, meaningless, everywhere. One entrance moment per page.
- **Parallax on everything**, or parallax deep enough to detach content from scroll position.
- **Scroll-jacking**: overriding wheel delta, forced section snapping the user fights, hijacked momentum. (Lenis smoothing ≠ jacking; changing *what* scroll does is.)
- **Loader/intro screens** on a document. It's a report, not a film festival.
- **Autoplaying infinite loops adjacent to body text** (readers can't read next to permanent movement — pause ambient loops when off-viewport via IntersectionObserver, and always under reduced-motion).
- **Bounce/elastic easing on serious content**; `linear` easing on anything but marquees/spinners.
- Durations: UI micro 150–250 ms · entrances 300–600 ms · anything over 800 ms had better be a scroll-scrubbed scene.

## Performance floor

`transform`/`opacity` only (no top/left/width) · `will-change` on at most 2–3 elements · IntersectionObserver to start and STOP work off-screen · total motion JS ≤ ~60 KB (GSAP core+ScrollTrigger ≈ 45 KB min+gzip) unless the artifact is an experience-tier showpiece.

**Verifying animated pages (validated):** headless-render once with `--force-prefers-reduced-motion` (must show the complete static page — proves the guard fires) and once from a copy with `<script>` tags stripped (must be missing nothing — proves the fail-safe). Don't trust `--virtual-time-budget` to settle rAF/GSAP entrances; it doesn't.
