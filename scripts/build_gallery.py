"""Rebuild the gallery thumbnails and composite images from docs/gallery.

Usage:
    PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/artifold/browsers \
        .venv/bin/python scripts/build_gallery.py [--skip-thumbs]

Making the pages themselves (run each prompt in prompts.json twice) is
manual. Do the craft runs against an empty library, never your own: the
skill reads the library it can see, and a public page once came out
addressed to its author by name. Put a wrapper first on PATH:

    #!/bin/sh
    HOME=/path/to/empty-demo-home exec /path/to/.venv/bin/artifold "$@"

The plain side: `claude -p --disable-slash-commands "<prompt>..."`.
Afterwards, check `git status artifold/skills`: craft records the modes it
invents in references/modes.md.

Reads docs/gallery/prompts.json (topic names) and each
docs/gallery/<slug>/{default,craft}.html. Writes:
    docs/gallery/thumbs/<slug>-{default,craft}.jpg   1280x800 viewport, dpr 2
    docs/gallery/composite-11x.jpg                   all pairs + unused modes
    docs/gallery/composite-2x2.jpg                   four pairs
    docs/gallery/composite-pair-coffee.jpg           one pair
    docs/index.html                                  the generated GALLERY data block
The design mode label comes from each craft page's artifold:design-mode meta.
The "not pictured" list is every mode in the skill's modes.md that no page used.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
GALLERY = REPO / "docs" / "gallery"
THUMBS = GALLERY / "thumbs"
MODES_MD = REPO / "artifold" / "skills" / "craft" / "references" / "modes.md"
MODEL = "claude-opus-5-5"
SITE = "shubhamgoel27.github.io/artifold"

# Reading order for the 11-up grid (two pairs per row). The pairs with the
# widest gap lead; the close calls are still shown, further down.
GRID_ORDER = [
    "climate-in-7-charts", "coffee-tier-list",
    "sf-apartments", "slow-software-manifesto",
    "30-day-tracker", "git-survival-kit",
    "kid-morning-routine", "macintosh-1984",
    "yosemite-climbing", "transformers",
    "gemini-embedding-2",
]
FOUR_UP = ["climate-in-7-charts", "coffee-tier-list", "sf-apartments",
           "slow-software-manifesto"]
SINGLE = "coffee-tier-list"

if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path.home() / "Library/Caches/artifold/browsers")


def version() -> str:
    m = re.search(r'__version__\s*=\s*"([^"]+)"', (REPO / "artifold" / "__init__.py").read_text())
    return m.group(1) if m else "?"


def meta(path: Path, name: str) -> str | None:
    m = re.search(rf'<meta\s+name="artifold:{re.escape(name)}"\s+content="([^"]*)"', path.read_text(errors="ignore"))
    return html.unescape(m.group(1)) if m else None


def all_modes() -> list[str]:
    return re.findall(r"^\| `([a-z0-9-]+)` \|", MODES_MD.read_text(), flags=re.M)


def used_modes(slugs: list[str]) -> dict[str, str]:
    out = {}
    for s in slugs:
        raw = meta(GALLERY / s / "craft.html", "design-mode") or "unknown"
        out[s] = re.sub(r"\s*[(;,].*$", "", raw).strip()  # drop trailing notes
    return out


def shoot_thumbs(browser, slugs: list[str]) -> None:
    THUMBS.mkdir(exist_ok=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2,
                              color_scheme="light")
    page = ctx.new_page()
    for s in slugs:
        for side in ("default", "craft"):
            src = GALLERY / s / f"{side}.html"
            page.goto(src.as_uri(), wait_until="load")
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            page.evaluate("document.fonts && document.fonts.ready")
            page.wait_for_timeout(1500)
            out = THUMBS / f"{s}-{side}.jpg"
            page.screenshot(path=str(out), type="jpeg", quality=85)
            print("thumb", out.relative_to(REPO))
    ctx.close()


BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f9f8f5; color: #16181d; -webkit-font-smoothing: antialiased;
       font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", system-ui, sans-serif; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
img { display: block; width: 100%; aspect-ratio: 16 / 10; object-fit: cover; object-position: top; }
"""


def thumb(slug: str, side: str) -> str:
    return (THUMBS / f"{slug}-{side}.jpg").as_uri()


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def html_11x(slugs, names, modes, unused, total) -> str:
    n_modes = len(set(modes.values()))
    cells = []
    for s in slugs:
        cells.append(f"""
        <section class="pair">
          <div class="head"><h2>{esc(names[s])}</h2>
            <span class="mono mode">/craft · <b>{esc(modes[s])}</b></span></div>
          <div class="cols">
            <figure><figcaption class="mono tag">Default</figcaption><img src="{thumb(s, 'default')}"></figure>
            <figure><figcaption class="mono tag craft">/craft</figcaption><img src="{thumb(s, 'craft')}"></figure>
          </div>
        </section>""")
    chips = "".join(f'<span class="mono chip">{esc(m)}</span>' for m in unused)
    cells.append(f"""
        <section class="pair bench">
          <div class="head"><h2>+ {len(unused)} modes not pictured</h2>
            <span class="mono mode">/craft has {total} total</span></div>
          <div class="panel">
            <p class="lead">Not pictured:</p>
            <div class="chips">{chips}</div>
            <p class="note">Each page picked its own mode for its subject. No mode was assigned.</p>
            <p class="mono foot">{SITE} · pip install artifold</p>
          </div>
        </section>""")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}
body {{ width: 1200px; padding: 18px 14px 20px; }}
header {{ display: flex; justify-content: space-between; align-items: baseline;
          padding-bottom: 12px; border-bottom: 1px solid rgba(15,23,42,.12); margin-bottom: 16px; }}
h1 {{ font-size: 17px; font-weight: 700; letter-spacing: -.02em; }}
h1 em {{ color: #c1452a; font-weight: 600; }}
.hmeta {{ font-size: 6px; letter-spacing: .12em; text-transform: uppercase; color: #5d6679; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px 14px; }}
.head {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }}
h2 {{ font-size: 8.5px; font-weight: 640; letter-spacing: -.01em; }}
.mode {{ font-size: 5.5px; color: #94a3b8; }} .mode b {{ color: #16181d; font-weight: 600; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }}
figure img {{ border: .5px solid rgba(15,23,42,.14); }}
.tag {{ font-size: 5px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
        color: #b26a1e; margin-bottom: 3px; }}
.tag.craft {{ color: #2f7a4b; }}
.bench {{ display: flex; flex-direction: column; }}
.panel {{ flex: 1; border: .5px dashed rgba(15,23,42,.25); background: #f3f2ee; margin-top: 8px;
          padding: 10px 12px; display: flex; flex-direction: column; }}
.lead {{ font-size: 7px; color: #5d6679; margin-bottom: 4px; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 2.5px 3px; }}
.chip {{ font-size: 5px; color: #2b5d8a; background: rgba(43,93,138,.08); padding: 1.5px 3px; border-radius: 1.5px; }}
.note {{ font-size: 6px; color: #5d6679; margin-top: 6px; }}
.foot {{ margin-top: auto; font-size: 6px; color: #16181d; }}
</style></head><body>
<header><h1>Same prompt. <em>Different output.</em></h1>
<span class="mono hmeta">{len(slugs)} topics · {n_modes} design modes · {MODEL} · artifold v{version()}</span></header>
<div class="grid">{''.join(cells)}</div></body></html>"""


def html_small(slugs, names, modes, width, sub) -> str:
    cols = 2 if len(slugs) > 1 else 1
    cells = []
    for s in slugs:
        label = (f'<p class="label">{esc(names[s])} <span>/craft = {esc(modes[s])}</span></p>'
                 if len(slugs) > 1 else "")
        cells.append(f"""
        <section>
          {label}
          <div class="cols">
            <figure><img src="{thumb(s, 'default')}"><span class="badge">default</span></figure>
            <figure><img src="{thumb(s, 'craft')}"><span class="badge craft">/craft</span></figure>
          </div>
        </section>""")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}
body {{ width: {width}px; padding: 14px 12px 12px; }}
h1 {{ font-size: 16px; font-weight: 450; letter-spacing: -.02em; }}
.sub {{ font-size: 5.5px; color: #5d6679; margin: 3px 0 9px; }}
.grid {{ display: grid; grid-template-columns: repeat({cols}, 1fr); gap: 12px 10px; }}
.label {{ font-size: 6.5px; margin-bottom: 6px; }} .label span {{ margin-left: 3px; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }}
figure {{ position: relative; }}
.badge {{ position: absolute; left: 0; bottom: 0; font-size: 4.5px; color: #fff; background: #16181d;
          padding: 3px 7px; border-radius: 0 1.5px 0 0; }}
.badge.craft {{ background: #c1452a; }}
</style></head><body>
<h1>Same prompt. Different output.</h1>
<p class="sub">{esc(sub)}</p>
<div class="grid">{''.join(cells)}</div></body></html>"""


def render(browser, doc: str, width: int, out: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(doc)
        tmp = Path(f.name)
    ctx = browser.new_context(viewport={"width": width, "height": 100}, device_scale_factor=2,
                              color_scheme="light")
    page = ctx.new_page()
    page.goto(tmp.as_uri(), wait_until="load")
    page.wait_for_timeout(300)
    page.screenshot(path=str(out), type="jpeg", quality=88, full_page=True)
    ctx.close()
    tmp.unlink()
    print("composite", out.relative_to(REPO))


def update_index(slugs, prompts, modes, mode_total) -> None:
    index = REPO / "docs" / "index.html"
    topics = []
    for s in slugs:
        craft = GALLERY / s / "craft.html"
        topics.append({
            "slug": s,
            "name": html.escape(prompts[s]["name"]),
            "prompt": html.escape(prompts[s]["prompt"]),
            "mode": modes[s],
            "layout": meta(craft, "layout-archetype") or "",
            "voice": meta(craft, "voice-register") or "",
        })
    data = {"model": MODEL, "version": version(), "modeTotal": mode_total, "topics": topics}
    block = ("  // gallery:data start (generated by scripts/build_gallery.py)\n"
             f"  const GALLERY = {json.dumps(data, indent=2, ensure_ascii=False)};\n"
             "  // gallery:data end")
    text = index.read_text()
    new, n = re.subn(r"  // gallery:data start.*?// gallery:data end", lambda _: block, text, flags=re.S)
    if n != 1:
        raise SystemExit("docs/index.html: gallery:data markers not found")
    index.write_text(new)
    print("index", index.relative_to(REPO))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skip-thumbs", action="store_true", help="reuse existing thumbs")
    args = ap.parse_args()

    prompts = json.loads((GALLERY / "prompts.json").read_text())
    names = {s: v["name"] for s, v in prompts.items()}
    slugs = [s for s in GRID_ORDER if (GALLERY / s / "craft.html").exists()]
    modes = used_modes(slugs)
    catalog = all_modes()
    unused = [m for m in catalog if m not in {p for v in modes.values() for p in re.split(r"\s*[x×]\s*", v)}]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        if not args.skip_thumbs:
            shoot_thumbs(browser, slugs)
        render(browser, html_11x(slugs, names, modes, unused, len(catalog)), 1200, GALLERY / "composite-11x.jpg")
        render(browser, html_small(FOUR_UP, names, modes, 1584,
                                   f"{MODEL} · {len(FOUR_UP)} prompts × 2 runs (default Claude vs /craft skill) · {SITE}"),
               1584, GALLERY / "composite-2x2.jpg")
        render(browser, html_small([SINGLE], names, modes, 1325,
                                   f"{names[SINGLE]} · /craft = {modes[SINGLE]} · {MODEL} · {SITE}"),
               1325, GALLERY / "composite-pair-coffee.jpg")
        browser.close()
    update_index(slugs, prompts, modes, len(catalog))
    for s in slugs:
        print(f"  {s:26s} {modes[s]}")


if __name__ == "__main__":
    main()
