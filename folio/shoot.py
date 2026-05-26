"""Screenshot each project's primary file with Playwright.

Cache key = sha1(path + mtime + size); thumbnails live under
`<cache>/thumbs/<key>.jpg`. Only new/changed primaries are re-shot.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

from .paths import BROWSERS, MANIFEST, THUMBS, ensure_dirs


def _key(path: str, mtime: float, size: int) -> str:
    return hashlib.sha1(f"{path}|{int(mtime)}|{size}".encode()).hexdigest()[:16]


def resolve_cached_thumbs(projects: list[dict]) -> list[tuple]:
    """Point each project at its cached thumb if present.
    Returns (proj, path, key, rel_thumb) tuples for projects still missing one."""
    ensure_dirs()
    missing = []
    for proj in projects:
        p = Path(proj["primary"]["path"])
        if not p.exists():
            proj["thumb"] = None
            continue
        st = p.stat()
        k = _key(proj["primary"]["path"], st.st_mtime, st.st_size)
        rel = f"thumbs/{k}.jpg"
        if (THUMBS / f"{k}.jpg").exists():
            proj["thumb"] = rel
        else:
            proj["thumb"] = None
            missing.append((proj, p, k, rel))
    return missing


def _ensure_chromium() -> bool:
    """Install playwright chromium-headless-shell if missing. Returns True on success.

    We install only the headless shell, not full chromium — Folio always launches
    headless, and the shell is ~170 MB vs ~290 MB for the full browser. Saves
    ~120 MB on disk for every Folio install. Idempotent: fast when already present.
    """
    BROWSERS.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSERS))
    try:
        import subprocess
        proc = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium-headless-shell"],
            capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr)
            return False
        return True
    except Exception as e:
        print(f"  ! could not install chromium: {e}", file=sys.stderr)
        return False


async def shoot(projects: list[dict], concurrency: int = 5) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ! playwright not installed — skipping screenshots.\n"
              "    pip install playwright && python -m playwright install chromium",
              file=sys.stderr)
        return

    if not _ensure_chromium():
        return

    ensure_dirs()
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    todo = resolve_cached_thumbs(projects)

    if not todo:
        print("  all thumbnails cached, nothing to shoot.")
        return

    print(f"  shooting {len(todo)} new/changed thumbnails (concurrency={concurrency})…")
    sem = asyncio.Semaphore(concurrency)
    done = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()

        async def one(proj, path, k, rel_thumb):
            nonlocal done
            async with sem:
                page = await browser.new_page(viewport={"width": 1280, "height": 800},
                                              device_scale_factor=1)
                try:
                    await page.goto(path.as_uri(), wait_until="load", timeout=20000)
                    await page.wait_for_timeout(900)
                    await page.screenshot(path=str(THUMBS / f"{k}.jpg"), type="jpeg",
                                          quality=72,
                                          clip={"x": 0, "y": 0, "width": 1280, "height": 800})
                    proj["thumb"] = rel_thumb
                    manifest[proj["id"]] = {"path": proj["primary"]["path"],
                                            "thumb": rel_thumb}
                except Exception as e:
                    proj["thumb"] = None
                    print(f"    ! {path.name}: {type(e).__name__}", file=sys.stderr)
                finally:
                    await page.close()
                    done += 1
                    if done % 20 == 0 or done == len(todo):
                        print(f"    {done}/{len(todo)}")

        await asyncio.gather(*(one(*t) for t in todo))
        await browser.close()

    MANIFEST.write_text(json.dumps(manifest, indent=2))
