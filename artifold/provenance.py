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
