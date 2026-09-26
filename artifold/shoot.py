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
import time
from pathlib import Path

from .paths import BROWSERS, MANIFEST, THUMBS, ensure_dirs


# Thumbnails render the page at a 1280x800 CSS viewport but capture at half
# resolution: 640x400. A card shows them 301px wide, so 640 is still sharp on
# a Retina screen, and each file drops from ~66 KB to ~23 KB. THUMB_V is part
# of the cache key so changing either constant regenerates every thumbnail
# once instead of leaving a mix of sizes.
THUMB_SCALE = 0.5
THUMB_V = 2


def _key(path: str, mtime: float, size: int) -> str:
    return hashlib.sha1(
        f"{path}|{int(mtime)}|{size}|v{THUMB_V}".encode()).hexdigest()[:16]


def resolve_cached_thumbs(projects: list[dict],
                          settle: float = 0.0) -> tuple[list[tuple], int]:
    """Point each project at a thumbnail. Returns (todo, deferred).

    `todo` holds (proj, path, key, rel_thumb) for projects that need a shoot
    now. With `settle` > 0, a project that already has a thumbnail and whose
    file changed less than `settle` seconds ago keeps showing that previous
    thumbnail and is not shot yet; `deferred` counts those. The key is
    path+mtime+size, so without this every save of an artifact being
    iterated on launched Chromium again: one artifact reached 44 revisions,
    which was 44 browser runs. Brand-new artifacts are always shot at once,
    so a new card never sits without a preview.
    """
    ensure_dirs()
    manifest = {}
    if settle and MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text())
        except Exception:
            manifest = {}
    now = time.time()
    todo, deferred = [], 0
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
            continue
        prev = (manifest.get(proj["id"]) or {}).get("thumb")
        if (settle and prev and (THUMBS / Path(prev).name).exists()
                and now - st.st_mtime < settle):
            proj["thumb"] = prev          # slightly stale, but not blank
            deferred += 1
            continue
        proj["thumb"] = None
        todo.append((proj, p, k, rel))
    return todo, deferred


def gc_thumbs(projects: list[dict]) -> tuple[int, int]:
    """Delete thumbnails and manifest rows no project points at.

    The cache key is sha1(path+mtime+size), so every edit writes a new
    thumbnail and strands the old one. Nothing deleted them: after three
    months a 133-project library held 513 files, 380 of them orphans, and
    32 MB of the 44 MB total. Full scans only — a partial scan does not
    know about the projects it did not look at.

    Returns (files_deleted, bytes_freed).
    """
    ensure_dirs()
    keep = {Path(p["thumb"]).name for p in projects if p.get("thumb")}
    deleted = freed = 0
    for f in THUMBS.glob("*.jpg"):
        if f.name in keep:
            continue
        try:
            size = f.stat().st_size
            f.unlink()
        except OSError:
            continue
        deleted += 1
        freed += size

    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text())
        except Exception:
            manifest = {}
        ids = {p["id"] for p in projects}
        pruned = {k: v for k, v in manifest.items() if k in ids}
        if len(pruned) != len(manifest):
            MANIFEST.write_text(json.dumps(pruned, indent=2))
    return deleted, freed


def ensure_chromium(force: bool = False) -> bool:
    """Install playwright chromium-headless-shell if missing. Returns True on success.

    We install only the headless shell, not full chromium — Artifold always launches
    headless, and the shell is ~170 MB vs ~290 MB for the full browser. Saves
    ~120 MB on disk for every Artifold install. Idempotent: fast when already present.

    Public so pdf.py / future Playwright callers can reuse this rather than
    each re-implementing the "auto-install on first use" logic.
    """
    BROWSERS.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSERS))
    # Fast path: the shell is already on disk. `playwright install` is
    # idempotent but spawns a whole Python + driver process to say so (~0.3s
    # per shoot). If a Playwright upgrade wants a newer revision, the launch
    # fails and `shoot` calls back here with force=True.
    if not force and any(BROWSERS.glob("chromium_headless_shell-*/*")):
        return True
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


async def shoot(projects: list[dict], concurrency: int = 5,
                settle: float = 0.0) -> int:
    """Shoot missing thumbnails. Returns how many were deferred by `settle`
    (see resolve_cached_thumbs); the caller rescans once they are quiet."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ! playwright not installed — skipping screenshots.\n"
              "    pip install playwright && python -m playwright install chromium",
              file=sys.stderr)
        return 0

    # Work out what needs shooting *before* touching the browser. Most scans
    # shoot nothing, and `ensure_chromium` spawns a `playwright install`
    # subprocess every time it is called — paid on every rescan for nothing.
    ensure_dirs()
    todo, deferred = resolve_cached_thumbs(projects, settle=settle)
    if deferred:
        print(f"  {deferred} thumbnail(s) still being edited; "
              f"reshooting once they settle.")

    if not todo:
        if not deferred:
            print("  all thumbnails cached, nothing to shoot.")
        return deferred

    if not ensure_chromium():
        return deferred

    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

    print(f"  shooting {len(todo)} new/changed thumbnails (concurrency={concurrency})…")
    sem = asyncio.Semaphore(concurrency)
    done = 0

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.launch()
        except Exception:
            # The fast path trusted an on-disk shell that this Playwright
            # version can't use. Install the right one and try once more.
            if not ensure_chromium(force=True):
                return deferred
            browser = await pw.chromium.launch()

        async def one(proj, path, k, rel_thumb):
            nonlocal done
            async with sem:
                page = await browser.new_page(viewport={"width": 1280, "height": 800},
                                              device_scale_factor=THUMB_SCALE)
                try:
                    # `networkidle` catches CDN font/CSS loads that `load`
                    # misses (matters for multi-file projects referencing
                    # Google Fonts etc). Fall back to `load` if networkidle
                    # stalls — some pages have long-poll sockets.
                    try:
                        await page.goto(path.as_uri(),
                                        wait_until="networkidle", timeout=12000)
                    except Exception:
                        await page.goto(path.as_uri(),
                                        wait_until="load", timeout=20000)
                    await page.wait_for_timeout(1500)  # JS hydration settle
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
    return deferred
