"""Fetch a shared AI-artifact URL → save the rendered HTML locally with
auto-populated provenance.

Works for *public share* URLs (Playwright renders client-side SPAs); rejects
*private chat* URLs (auth-walled) with a helpful pointer to `artifold link`.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from . import config, provenance

# Chat URLs require auth → we can't fetch them headless. Tell the user.
PRIVATE_CHAT_PATTERNS = [
    re.compile(r"^https?://claude\.ai/(chat|new)/", re.I),
    re.compile(r"^https?://chatgpt\.com/c/", re.I),
    re.compile(r"^https?://gemini\.google\.com/app", re.I),
]


def _tool_from_url(url: str) -> str | None:
    host = (urlparse(url).hostname or "").lower()
    if "claude.ai" in host:      return "claude"
    if "chatgpt.com" in host or "openai.com" in host: return "chatgpt"
    if "v0.dev" in host:         return "v0"
    if "lovable.dev" in host or "lovable.app" in host: return "lovable"
    if "bolt.new" in host or "bolt.dev" in host: return "bolt"
    if "gemini.google" in host:  return "gemini"
    if "cursor" in host:         return "cursor"
    return None


def _safe_filename(s: str, fallback: str) -> str:
    """Date-prefixed kebab-case filename to match the convention used
    everywhere else (so Finder sorts naturally by recency)."""
    from datetime import datetime
    s = re.sub(r"[^\w\s.-]", "", (s or "")).strip()
    s = re.sub(r"\s+", "-", s)
    s = s[:60].strip("-.") or fallback
    if s.endswith(".html"):
        s = s[:-5]
    date = datetime.now().strftime("%Y-%m-%d")
    return f"{date}-{s.lower()}.html"


def _ensure_drop_dir(cfg: dict) -> Path:
    """Resolve the dir where imported artifacts land. Auto-creates
    ~/artifold-inbox and adds it as a root if `drop_dir` isn't configured."""
    if cfg.get("drop_dir"):
        p = Path(cfg["drop_dir"]).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    p = (Path.home() / "artifold-inbox").resolve()
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        print(f"  (created drop dir {p})")
    roots = [str(Path(r).resolve()) for r in (cfg.get("roots") or [])]
    if str(p) not in roots:
        config.add_root(p)
        print(f"  (added {p} as a Artifold root so imports get indexed)")
    # persist drop_dir so we don't re-add the root on every import
    fresh = config.load()
    fresh["drop_dir"] = str(p)
    config.save(fresh)
    return p


def import_url(url: str, name: str | None = None,
               drop_dir: str | None = None) -> Path | None:
    cfg = config.load()

    for pat in PRIVATE_CHAT_PATTERNS:
        if pat.match(url):
            print(f"  ! {url}")
            print(f"    looks like a private chat URL — these need login to view.")
            print(f"    save the artifact HTML manually (download / export), then:")
            print(f"      artifold link <file> --source {url} --tool {_tool_from_url(url) or '<tool>'}")
            return None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ! artifold import requires playwright (a core Artifold dep).")
        return None

    dd = Path(drop_dir).expanduser().resolve() if drop_dir else _ensure_drop_dir(cfg)
    dd.mkdir(parents=True, exist_ok=True)

    print(f"  fetching {url} …")
    title = ""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            try:
                page.goto(url, wait_until="networkidle", timeout=25000)
                page.wait_for_timeout(1500)   # let SPAs settle
                html = page.content()
                title = (page.title() or "").strip()
            except Exception as e:
                print(f"  ! fetch failed: {type(e).__name__}: {e}")
                browser.close()
                return None
            browser.close()
    except Exception as e:
        print(f"  ! playwright failed: {type(e).__name__}: {e}")
        return None

    fname = _safe_filename(name or title, "imported")
    out = dd / fname
    i = 2
    while out.exists():
        stem = fname[:-5]
        out = dd / f"{stem}-{i}.html"
        i += 1
    out.write_text(html, encoding="utf-8")
    print(f"  saved → {out}  ({len(html):,} bytes)")

    tool = _tool_from_url(url)
    sha = provenance.sha1_of(out)
    fields = {"source": url, "intent_source": "user"}
    if tool:
        fields["tool"] = tool
    provenance.set_(sha, **fields)
    print(f"  linked → tool={tool!r}, source={url}")
    print(f"  next: run `artifold scan` to index it into the dashboard.")
    return out
