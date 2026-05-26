"""Render the static dashboard (data.json + index.html) into the cache dir."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib import resources

from .paths import DATA, INDEX, ensure_dirs


def build(projects: list[dict], roots: list[str]) -> dict:
    ensure_dirs()
    cats = sorted({p["category"] for p in projects})
    counts = {c: sum(1 for p in projects if p["category"] == c) for c in cats}
    total_files = sum(p["file_count"] for p in projects)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roots": [str(r) for r in roots],
        "categories": cats,
        "counts": counts,
        "projects": projects,
    }
    DATA.write_text(json.dumps(payload, separators=(",", ":")))

    tpl = resources.files("folio").joinpath("template.html").read_text(encoding="utf-8")
    INDEX.write_text(tpl
                     .replace("__DATA__", json.dumps(payload, separators=(",", ":")))
                     .replace("__TOTAL_PROJ__", str(len(projects)))
                     .replace("__TOTAL_FILES__", str(total_files)))
    print(f"  built {INDEX}  ({len(projects)} projects, {total_files} files)")
    return payload
