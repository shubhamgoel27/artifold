"""Persistent per-artifact metadata, keyed by content hash.

Keyed by SHA1(content) so a file moving / being renamed doesn't lose its
source / prompt / tags / model. The store lives in the cache dir:
`<cache>/provenance.json`. Schema is versioned for future migrations.

Each entry shape:
    {
      "source":   "https://claude.ai/share/...",  // chat or artifact URL
      "tool":     "claude" | "chatgpt" | "v0" | "lovable" | "bolt" | "gemini"
                  | "manual" | null,
      "model":    "claude-opus-4-7" | null,
      "prompt":   "<the prompt that made it>" | null,
      "tags":     [],
      "notes":    "",
      "added_at": "<iso>"
    }
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .paths import CACHE_DIR, ensure_dirs

SCHEMA = 1
STORE = CACHE_DIR / "provenance.json"

VALID_TOOLS = {"claude", "chatgpt", "v0", "lovable", "bolt", "gemini",
               "cursor", "manual", None}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_raw() -> dict:
    if not STORE.exists():
        return {"version": SCHEMA, "items": {}}
    try:
        d = json.loads(STORE.read_text())
    except Exception:
        return {"version": SCHEMA, "items": {}}
    if d.get("version") != SCHEMA:
        # future migrations land here
        d.setdefault("items", {})
        d["version"] = SCHEMA
    return d


def _save_raw(d: dict) -> None:
    ensure_dirs()
    STORE.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")


def get(sha: str) -> dict | None:
    return _load_raw()["items"].get(sha)


def set_(sha: str, **fields) -> dict:
    """Upsert provenance fields for a content hash. Unknown keys are kept."""
    d = _load_raw()
    cur = d["items"].setdefault(sha, {"added_at": _now()})
    if "tool" in fields and fields["tool"] not in VALID_TOOLS:
        raise ValueError(f"tool must be one of {sorted(t for t in VALID_TOOLS if t)}")
    for k, v in fields.items():
        if v is None:
            continue
        if k == "tags" and isinstance(v, list):
            cur["tags"] = sorted(set((cur.get("tags") or []) + v))
        else:
            cur[k] = v
    _save_raw(d)
    return cur


def annotate_path(path: Path, **fields) -> tuple[str, dict]:
    """Convenience: compute hash for a path, then set_(). Returns (sha, entry)."""
    sha = sha1_of(path)
    entry = set_(sha, **fields)
    return sha, entry


def all_items() -> dict[str, dict]:
    return dict(_load_raw()["items"])


def carry_forward(new_sha: str, path: Path) -> dict | None:
    """A file was edited in place: its content hash changed, so the old
    entry no longer matches. Copy the old entry (found by `path`, recorded
    at scan time) onto the new hash so source/prompt/tags/shares survive
    edits, not just moves. The old entry is marked superseded (GC'd later,
    so a Trash-restore of the old content still reattaches within the TTL).
    Returns the new entry, or None if there was nothing to carry."""
    d = _load_raw()
    items = d["items"]
    if new_sha in items:
        return items[new_sha]
    p = str(path)
    old_sha = next((s for s, e in items.items()
                    if e.get("path") == p and not e.get("superseded_by")), None)
    if not old_sha:
        return None
    fresh = dict(items[old_sha])
    fresh.pop("superseded_by", None)
    fresh.pop("orphaned_at", None)
    fresh["previous_sha"] = old_sha
    items[new_sha] = fresh
    items[old_sha]["superseded_by"] = new_sha
    _save_raw(d)
    return fresh


ORPHAN_TTL_DAYS = 30


def gc(active_shas: set[str]) -> int:
    """Reconcile the store against a full scan. Entries whose hash wasn't
    seen get stamped `orphaned_at` (and dropped after ORPHAN_TTL_DAYS);
    entries seen again get the stamp cleared (Trash restore, git checkout).
    Returns the number of entries deleted."""
    d = _load_raw()
    items = d["items"]
    now = datetime.now(timezone.utc)
    deleted = 0
    for sha in list(items):
        e = items[sha]
        if sha in active_shas:
            e.pop("orphaned_at", None)   # re-seen: un-orphan
            continue
        # Not in the scan, but its file still exists and no newer content
        # took over the path (variants, depth-excluded or hand-linked
        # files land here). Leave them alone.
        p = e.get("path")
        if p and not e.get("superseded_by") and Path(p).is_file():
            e.pop("orphaned_at", None)
            continue
        stamp = e.get("orphaned_at")
        if not stamp:
            e["orphaned_at"] = now.isoformat(timespec="seconds")
            continue
        try:
            age = now - datetime.fromisoformat(stamp)
        except ValueError:
            e["orphaned_at"] = now.isoformat(timespec="seconds")
            continue
        if age.days >= ORPHAN_TTL_DAYS:
            del items[sha]
            deleted += 1
    _save_raw(d)
    return deleted
