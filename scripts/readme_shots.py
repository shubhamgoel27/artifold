"""Rebuild the README's dashboard screenshots and demo GIF.

Everything runs against a throwaway library made from the gallery pages,
under its own HOME, so nothing from your real library can end up in a
public image. Each gallery topic becomes one artifact with two versions:
the plain page as v1 and the craft page as v2.

    .venv/bin/python scripts/readme_shots.py

Writes docs/demo.gif, docs/cmdk.png and docs/share-detail.png.
Needs ffmpeg for the GIF.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "docs" / "gallery"
DOCS = ROOT / "docs"
PORT = 8799
VIEW = {"width": 1500, "height": 940}

# Readable file names, the way they would land in a downloads folder.
NAMES = {
    "30-day-tracker": "strength-tracker",
    "climate-in-7-charts": "climate-in-seven-charts",
    "coffee-tier-list": "sf-coffee-tier-list",
    "gemini-embedding-2": "gemini-embedding-2-explainer",
    "git-survival-kit": "git-survival-kit",
    "kid-morning-routine": "morning-routine",
    "macintosh-1984": "original-macintosh",
    "sf-apartments": "apartment-comparison",
    "slow-software-manifesto": "slow-software-manifesto",
    "transformers": "transformers-explainer",
    "yosemite-climbing": "yosemite-climbing-routes",
}


def build_library(home: Path) -> Path:
    lib = home / "Documents" / "ai-pages"
    lib.mkdir(parents=True)
    now = time.time()
    for i, (slug, name) in enumerate(NAMES.items()):
        src = GALLERY / slug
        if not (src / "craft.html").exists():
            continue
        # Spread edits over the last few weeks so dates and sorting look real.
        v1, v2 = lib / f"{name}.html", lib / f"{name}-v2.html"
        shutil.copy(src / "default.html", v1)
        shutil.copy(src / "craft.html", v2)
        t = now - (i * 2.3 + 1) * 86400
        os.utime(v1, (t - 3 * 86400, t - 3 * 86400))
        os.utime(v2, (t, t))
    return lib


def env_for(home: Path) -> dict:
    env = dict(os.environ, HOME=str(home))
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def setup_home(home: Path, lib: Path) -> None:
    cache = home / "Library" / "Caches" / "artifold"
    cache.mkdir(parents=True)
    real = Path.home() / "Library" / "Caches" / "artifold" / "browsers"
    if real.is_dir():
        (cache / "browsers").symlink_to(real)
    cfg = home / "Library" / "Application Support" / "artifold"
    cfg.mkdir(parents=True)
    (cfg / "config.json").write_text(json.dumps({"roots": [str(lib)]}))


def wait_up(url: str, timeout: float = 30) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except Exception:
            time.sleep(0.3)
    sys.exit(f"server did not come up at {url}")


def shoot(base: str, frames_dir: Path) -> None:
    from playwright.sync_api import sync_playwright
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH",
                          str(Path.home() / "Library/Caches/artifold/browsers"))
    frames: list[Path] = []

    def frame(page, hold: int = 1):
        for _ in range(hold):
            p = frames_dir / f"{len(frames):04d}.png"
            page.screenshot(path=str(p))
            frames.append(p)

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport=VIEW, device_scale_factor=2,
                          color_scheme="dark")
        page.goto(base, wait_until="load")
        page.wait_for_selector(".card")
        page.wait_for_timeout(800)

        # 1. The grid.
        frame(page, 6)

        # 2. Search narrows as you type.
        page.click("#q")
        for ch in "coffee":
            page.keyboard.type(ch)
            page.wait_for_timeout(120)
            frame(page)
        frame(page, 5)
        page.fill("#q", "")
        page.wait_for_timeout(300)
        frame(page, 2)

        # 3. The command palette.
        page.keyboard.press("Escape")
        page.keyboard.press("Meta+k")
        page.wait_for_selector("#cmdk", state="visible")
        page.wait_for_timeout(300)
        for ch in "climb":
            page.keyboard.type(ch)
            page.wait_for_timeout(120)
            frame(page)
        frame(page, 4)
        page.screenshot(path=str(DOCS / "cmdk.png"))

        # 4. Open it: preview with the version picker.
        page.keyboard.press("Enter")
        page.wait_for_selector("#detail", state="visible")
        page.wait_for_timeout(1500)
        frame(page, 6)
        page.screenshot(path=str(DOCS / "share-detail.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        frame(page, 3)
        b.close()

    gif = DOCS / "demo.gif"
    pal = frames_dir / "pal.png"
    pattern = str(frames_dir / "%04d.png")
    scale = "fps=4,scale=1200:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "4",
                    "-i", pattern, "-vf", f"{scale},palettegen=max_colors=192",
                    str(pal)], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "4",
                    "-i", pattern, "-i", str(pal), "-lavfi",
                    f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                    str(gif)], check=True)
    print(f"  wrote {gif.relative_to(ROOT)} ({gif.stat().st_size // 1024} KB), "
          f"{len(frames)} frames")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="artifold-demo-"))
    home = tmp / "home"
    lib = build_library(home)
    setup_home(home, lib)
    env = env_for(home)
    exe = str(ROOT / ".venv" / "bin" / "artifold")
    subprocess.run([exe, "scan"], env=env, check=True)
    server = subprocess.Popen([exe, "serve", "--no-open", "--port", str(PORT)],
                              env=env, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{PORT}/"
        wait_up(base)
        frames = tmp / "frames"
        frames.mkdir()
        shoot(base, frames)
        print("  wrote docs/cmdk.png, docs/share-detail.png")
    finally:
        server.terminate()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
