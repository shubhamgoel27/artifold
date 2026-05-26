"""Publish a single artifact to a public URL via GitHub Pages.

Default backend: GitHub Pages via the `gh` CLI (which most devs already have
authed). Uses one repo per user — `<user>/artifold-share` — and writes each
shared artifact as `<short-sha>.html`. Idempotent: re-sharing the same file
returns the same URL.

What gets exposed: only the artifact you call `share` on. Your local library,
provenance store, and config never leave your disk.

Cloudflare Pages backend is planned (v0.3-beta) for users without `gh`.
"""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import provenance
from .paths import CACHE_DIR, ensure_dirs

SHARE_REPO_NAME = "artifold-share"
SHARE_REPO_DIR = CACHE_DIR / "share-repo"


def _run(cmd: list[str], cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True,
                          cwd=str(cwd) if cwd else None, check=check)


def _gh(*args: str) -> subprocess.CompletedProcess:
    return _run(["gh", *args])


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return _run(["git", *args], cwd=cwd)


def _gh_authed() -> bool:
    return _gh("auth", "status").returncode == 0


def _gh_user() -> str | None:
    r = _gh("api", "user", "--jq", ".login")
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def _repo_exists(user: str) -> bool:
    return _gh("repo", "view", f"{user}/{SHARE_REPO_NAME}").returncode == 0


def _create_repo(user: str) -> bool:
    print(f"  creating public repo {user}/{SHARE_REPO_NAME}…")
    r = _gh("repo", "create", SHARE_REPO_NAME,
            "--public",
            "--description", "Artifold shared artifacts (managed by the artifold CLI).",
            "--clone=false")
    if r.returncode != 0:
        print(f"  ! repo create failed: {r.stderr.strip()}")
        return False
    return True


def _enable_pages(user: str) -> bool:
    """Enable GH Pages on main / root. Idempotent — 409 if already on."""
    r = _gh("api", f"/repos/{user}/{SHARE_REPO_NAME}/pages")
    if r.returncode == 0:
        return True
    r = _gh("api", "-X", "POST",
            f"/repos/{user}/{SHARE_REPO_NAME}/pages",
            "-f", "source[branch]=main", "-f", "source[path]=/")
    return r.returncode == 0


def _bootstrap_repo(user: str, repo_dir: Path) -> bool:
    """First-time clone + commit a minimal index.html so Pages has content."""
    ensure_dirs()
    if repo_dir.exists():
        import shutil
        shutil.rmtree(repo_dir)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    clone = _git("clone", f"git@github.com:{user}/{SHARE_REPO_NAME}.git",
                 str(repo_dir))
    if clone.returncode != 0:
        # try https as a fallback (works without ssh keys set up)
        clone = _git("clone",
                     f"https://github.com/{user}/{SHARE_REPO_NAME}.git",
                     str(repo_dir))
    if clone.returncode != 0:
        print(f"  ! clone failed: {clone.stderr.strip()}")
        return False

    idx = repo_dir / "index.html"
    if not idx.exists():
        idx.write_text(
            "<!doctype html><meta charset=utf-8><title>Artifold shares</title>"
            "<body style='font:15px/1.5 -apple-system,sans-serif;"
            "max-width:560px;margin:60px auto;color:#222;padding:0 20px'>"
            "<h1>Artifold shares</h1>"
            "<p>This repo holds artifacts shared from a "
            "<a href='https://github.com/shubhamgoel27/artifold'>Artifold</a> library. "
            "Each share has its own URL — you reach it directly.</p>")
        _git("-c", "user.email=artifold@local", "-c", "user.name=Artifold",
             "add", "index.html", cwd=repo_dir)
        _git("-c", "user.email=artifold@local", "-c", "user.name=Artifold",
             "commit", "-q", "-m", "Initial: artifold share index", cwd=repo_dir)
        if _git("push", "origin", "HEAD:main", cwd=repo_dir).returncode != 0:
            # default branch may not be main yet; create it
            _git("branch", "-M", "main", cwd=repo_dir)
            _git("push", "-u", "origin", "main", cwd=repo_dir)
    return True


def _ensure_repo_clone(user: str) -> Path | None:
    """Ensure local clone of <user>/artifold-share is present and current."""
    if not _repo_exists(user):
        if not _create_repo(user):
            return None
        if not _bootstrap_repo(user, SHARE_REPO_DIR):
            return None
    elif not (SHARE_REPO_DIR / ".git").is_dir():
        if not _bootstrap_repo(user, SHARE_REPO_DIR):
            return None
    else:
        # Refresh
        _git("fetch", "--quiet", "origin", cwd=SHARE_REPO_DIR)
        _git("reset", "--quiet", "--hard", "origin/main", cwd=SHARE_REPO_DIR)
    return SHARE_REPO_DIR


def _wait_until_live(url: str, timeout: float = 90.0,
                     on_tick=None) -> bool:
    """HEAD the URL until it returns 200 or timeout elapses.
    GH Pages typically builds in 15–45s. Returns True if the page went live.
    `on_tick(elapsed_seconds)` is called every poll for progress UI."""
    deadline = time.time() + timeout
    interval = 2.5
    t0 = time.time()
    # Quick first check — if it's already live (idempotent re-share), skip the wait.
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=5) as r:
                if 200 <= r.status < 300:
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 200:
                return True
        except Exception:
            pass
        if on_tick:
            on_tick(time.time() - t0)
        time.sleep(interval)
    return False


def _copy_to_clipboard(text: str) -> bool:
    """Best-effort clipboard. macOS: pbcopy. Linux: xclip/xsel if present."""
    for cmd in (["pbcopy"], ["xclip", "-selection", "clipboard"], ["xsel", "-b", "-i"]):
        try:
            p = subprocess.run(cmd, input=text, text=True,
                               capture_output=True, timeout=3)
            if p.returncode == 0:
                return True
        except FileNotFoundError:
            continue
    return False


def share_via_gh(file: Path, no_clipboard: bool = False) -> str | None:
    file = file.expanduser().resolve()
    if not file.is_file():
        print(f"  ! not a file: {file}")
        return None

    # Preflight: surface any setup issues with specific fixes, instead of bailing
    # with cryptic gh errors.
    from . import diagnostics
    issues = diagnostics.share_preflight()
    if issues:
        print("`artifold share` needs a one-time setup before it works:\n")
        for c in issues:
            print(f"  {c.glyph} {c.name}: {c.message}")
            if c.fix:
                print(f"      → {c.fix}")
        print("\nfix those, then re-run.  (run `artifold doctor` any time.)")
        if _copy_to_clipboard(issues[0].fix or ""):
            print("(first fix command copied to clipboard)")
        return None

    user = _gh_user()
    if not user:
        print("  ! couldn't determine your github user via gh"); return None

    sha = provenance.sha1_of(file)
    entry = provenance.get(sha) or {}
    short_id = sha[:8]
    expected_url = f"https://{user}.github.io/{SHARE_REPO_NAME}/{short_id}.html"

    # Idempotent: if already published with this hash, just return the URL.
    existing = next((s for s in (entry.get("shares") or [])
                     if s.get("host") == "github_pages" and s.get("url") == expected_url),
                    None)
    if existing:
        print(f"  already shared (same content): {expected_url}")
        if not no_clipboard and _copy_to_clipboard(expected_url):
            print("  (URL copied to clipboard)")
        return expected_url

    print("  ⚠️  publishing to a PUBLIC URL anyone with the link can view")

    repo_dir = _ensure_repo_clone(user)
    if not repo_dir:
        return None
    if not _enable_pages(user):
        print("  ! could not enable GitHub Pages")
        return None

    dest = repo_dir / f"{short_id}.html"
    dest.write_bytes(file.read_bytes())
    _git("-c", "user.email=artifold@local", "-c", "user.name=Artifold",
         "add", f"{short_id}.html", cwd=repo_dir)
    _git("-c", "user.email=artifold@local", "-c", "user.name=Artifold",
         "commit", "-q", "-m", f"share {file.name}", cwd=repo_dir)
    push = _git("push", "--quiet", "origin", "main", cwd=repo_dir)
    if push.returncode != 0:
        print(f"  ! push failed: {push.stderr.strip()}")
        return None

    # Wait for GH Pages to actually build before declaring success.
    print(f"  waiting for GitHub Pages to build (15–60s)…", flush=True)
    def _progress(elapsed):
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            print(f"    still building… ({int(elapsed)}s)", flush=True)
    live = _wait_until_live(expected_url, timeout=120.0, on_tick=_progress)
    if not live:
        print(f"  ⚠  pushed but URL still 404 after 2 min — try again in a bit:")
        print(f"     {expected_url}")
        return None

    # Record share into provenance (only after we've confirmed it's actually live)
    shares = list(entry.get("shares") or [])
    shares.append({
        "host": "github_pages",
        "url": expected_url,
        "id": short_id,
        "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    provenance.set_(sha, shares=shares)

    print(f"  ✓ live: {expected_url}")
    if not no_clipboard and _copy_to_clipboard(expected_url):
        print("  (URL copied to clipboard)")
    return expected_url


def list_shares() -> list[dict]:
    items = provenance.all_items()
    out = []
    for sha, entry in items.items():
        for s in entry.get("shares") or []:
            out.append({"sha": sha, **s, "tool": entry.get("tool"),
                        "source": entry.get("source")})
    out.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return out


def revoke(short_id: str) -> bool:
    """Remove a previously-shared artifact (deletes the file from the repo)."""
    if not _gh_authed():
        print("  ! gh not authed"); return False
    user = _gh_user()
    if not user:
        return False
    repo_dir = _ensure_repo_clone(user)
    if not repo_dir:
        return False
    target = repo_dir / f"{short_id}.html"
    if not target.exists():
        print(f"  ! no share with id {short_id} in the repo")
        return False
    _git("rm", "--quiet", f"{short_id}.html", cwd=repo_dir)
    _git("-c", "user.email=artifold@local", "-c", "user.name=Artifold",
         "commit", "-q", "-m", f"revoke {short_id}", cwd=repo_dir)
    if _git("push", "--quiet", "origin", "main", cwd=repo_dir).returncode != 0:
        print("  ! push failed"); return False

    # Strip from provenance records
    for sha, entry in provenance.all_items().items():
        shares = entry.get("shares") or []
        new = [s for s in shares if s.get("id") != short_id]
        if len(new) != len(shares):
            provenance.set_(sha, shares=new)
    print(f"  revoked {short_id}")
    return True
