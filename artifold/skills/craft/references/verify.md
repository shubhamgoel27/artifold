# Verify: render mechanics, defect scan, and the art-director pass

The policy (tier gate, cycle caps, what blocks shipping) lives in SKILL.md section 10. This file is the how.

## 1 · Render everything in ONE Bash call

Each Bash call is a full agent turn, but a headless render takes about 1.3 s. Run the renders **one after another** in a single block. Two traps, both validated on this machine:
- **Never pass `--user-data-dir`.** A fresh profile makes headless Chrome hang forever. That is also why running renders in parallel "hung": each parallel render needed its own profile.
- **Write every flag out in full on each line.** Never bundle flags in a variable like `H="--headless ..."`: the Bash tool runs zsh, which passes `$H` as one argument, so Chrome drops `--headless` and opens tabs in the user's real browser.
- macOS has no `timeout` command. If you need one, use Python's `subprocess.run(..., timeout=30)`.

```bash
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; P=<scratchpad>/craft; ABS=<abs-path>
printf '<body style="margin:0"><iframe src="file://%s" style="width:375px;height:1600px;border:0;display:block"></iframe></body>' "$ABS" > $P-wrap.html
sed 's/<html\([^>]*\)>/<html\1 data-theme="light">/' "$ABS" > $P-forcelight.html
"$C" --headless --disable-gpu --hide-scrollbars --blink-settings=preferredColorScheme=1 --window-size=1440,900 --screenshot=$P-1440.png "file://$ABS" 2>/dev/null
"$C" --headless --disable-gpu --hide-scrollbars --blink-settings=preferredColorScheme=0 --window-size=1440,900 --screenshot=$P-1440-dark.png "file://$ABS" 2>/dev/null
"$C" --headless --disable-gpu --hide-scrollbars --blink-settings=preferredColorScheme=0 --window-size=1440,900 --screenshot=$P-1440-forcelight.png "file://$P-forcelight.html" 2>/dev/null
"$C" --headless --disable-gpu --hide-scrollbars --blink-settings=preferredColorScheme=1 --window-size=500,1600 --screenshot=$P-375.png "file://$P-wrap.html" 2>/dev/null
for f in 1440 1440-dark 1440-forcelight; do sips -Z 720 $P-$f.png --out $P-$f-s.png >/dev/null; done
sips -Z 200 $P-1440.png --out $P-squint.png >/dev/null
ls -la $P-*.png
```

Raise the window height (and the iframe height) to fit a long page in one shot.

- **Always set the color scheme explicitly** (validated on this machine): headless Chrome reports `prefers-color-scheme: dark` by default, so an unflagged render only ever shows the dark theme. `preferredColorScheme=1` is light, `=0` is dark.
- **The forced-light render is the one that catches real bugs:** a dark OS plus an explicit `data-theme="light"`. If it comes out dark, the `:root:not([data-theme="light"])` guard is missing. The sed line assumes a bare `<html lang=…>` tag; check the copy if the page's `<html>` already carries `data-theme`.
- **The 375 iframe wrapper is mandatory, not optional** (validated on this machine): headless Chrome enforces a ~500 px minimum window width, so `--window-size=375` silently lays out at 500 CSS px and crops the screenshot; sub-500 media queries never fire. The iframe genuinely constrains layout. Widths ≥ 500 are unaffected.
- **768 only on evidence:** render it only if the file has mid-range breakpoints (`grep -cE '@media[^{]*(min|max)-width:\s*([5-9][0-9]{2}|10[0-9]{2})px' <file>` nonzero) or the layout is a multi-column collapse risk (grid-of-tiles, split-screen, quadrant-map, magazine-spread). Fluid single-column/poster/single-object pages don't break between 1440 and 375.
- **Animated pages, two extra lines in the same block** (validated; `--virtual-time-budget` does NOT settle rAF/GSAP entrances, don't rely on it):
  - a render with `--force-prefers-reduced-motion` → must show the COMPLETE static page (proves the guard fires);
  - a render of a copy with all `<script>` tags stripped → must be missing nothing (proves the no-JS fail-safe; anything stuck at `opacity:0` is a Blocker).
- No Chrome at all → skip renders gracefully and tell the user it wasn't visually verified.

## 2 · Read downscales, not originals

Read the `-s.png` (720 px) copies for the defect scan (~450 tokens vs ~1.7k full-res; overflow, clipping, collisions, and hierarchy all survive the downscale). Open a full-res original only to confirm a suspected finding (contrast, hairlines, kerning). The art-director subagent always gets full-res paths.

## 3 · Defect checklist (run it yourself on the downscales)

Overlapping elements · text clipped at edges · overflow / horizontal scroll at 375 · colliding footers/labels · uneven or cramped gaps · low-contrast text/icons · leftover placeholder text · broken/empty SVG · an element positioned for one line whose text wrapped to two · **SVG `<text>` never wraps** (labels need a measured container or a shorter string, and an SVG that scales up on mobile scales its clipping with it, cap its width).

Triage Blocker / High / Medium / Nitpick. Fix every Blocker + High, then **re-render only the widths where findings lived**; do one full-width batch before the art-director pass so a cross-width regression can't ship.

## 4 · Typesetting scan (visible text only)

Run this on the finished file. It ignores `<head>`, `<style>`, and `<script>`, so every hit is something a reader will see. (An earlier grep version flagged the meta tags on every page and trained everyone to ignore it.)

```bash
python3 - <file.html> <<'PY'
import re, sys, html
src = open(sys.argv[1]).read()
body = re.sub(r'(?s)<(script|style|head)\b.*?</\1>', ' ', src)
issues = []
for m in re.finditer(r'>([^<>]+)<', body):
    t = html.unescape(m.group(1))
    if not t.strip(): continue
    line = src.count('\n', 0, src.find(m.group(1))) + 1
    for name, pat in [('straight quote', r'"'), ("straight apostrophe", r"[A-Za-z]'[A-Za-z]|'"),
                      ('three dots', r'\.\.\.'), ('x for times', r'\d ?[xX] ?\d'),
                      ('hyphen range', r'\d ?- ?\d'), ('em dash', '\u2014'), ('double hyphen', '--')]:
        if re.search(pat, t): issues.append(f'{line}: {name}: {t.strip()[:70]}')
print('\n'.join(issues) or 'clean: no typesetting issues in visible text')
PY
```

Pass condition: it prints `clean`. It cannot see missing `tabular-nums` or a missing no-break space between a number and its unit; check those two by eye.

## 5 · The one fresh-eyes pass (defects + rubric in a single subagent)

After your own Blocker/High fixes, hand the full-res screenshots (and the squint image) to ONE subagent playing a hard-to-please art director. Tell it nothing about your intent, if the intent doesn't read from pixels, that's the finding. It returns two sections:

- **(A) Defects you missed**, triaged Blocker/High/Medium/Nitpick.
- **(B) Rubric**, scored 1–5 with one-sentence justifications, and for every score ≤ 3 the specific named fix (element, property, direction):
  *instant hierarchy* (what reads first, second, third?) · *spacing rhythm* (one scale or arbitrary gaps?) · *typographic color* (do text blocks' grays balance?) · *palette dominance* (60/30/10 or everything loud?) · *craft detail* (real punctuation, aligned numerals, optical alignment, drawn-element quality) · *the portfolio test* (would a working designer claim this page?).

**Squint test** feeds the same pass: the 200 px downscale must keep one focal point; gray mush or three competing hotspots = hierarchy failure.

Apply the named fixes, re-render affected widths. **One cycle; a second only if any score is ≤ 2 after fixes.** Ship with scores noted, and record them in the `artifold:ad-scores` meta tag (SKILL.md section 11).
