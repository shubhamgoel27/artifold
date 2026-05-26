"""Artifold user config — roots to scan + small overrides.

config.json schema:
    {
      "roots": ["/Users/me/Downloads", "/Users/me/work"],
      "allow_repos": [],            # dir names with their own .git to include anyway
      "max_depth": 3,               # max nesting under a project dir
      "categories": { ... }         # optional override of DEFAULT_CATEGORIES
    }
"""
from __future__ import annotations

import json
from pathlib import Path

from .paths import CONFIG_FILE, ensure_dirs

# Sensible generic defaults — broad enough to cover most AI-generated artifacts.
DEFAULT_CATEGORIES = {
    "Engineering": ["code", "api", "agent", "ml ", "model", "pipeline", "algo",
                    "engineer", "system", "architecture", "infra", "devops",
                    "deploy", "kubernetes", "rl", "llm", "ai"],
    "Health":      ["health", "fitness", "workout", "training", "diet",
                    "nutrition", "medical", "wellness", "exercise", "tracker",
                    "sleep", "mental"],
    "Finance":     ["finance", "tax", "money", "budget", "invest", "credit",
                    "card", "loan", "retirement", "stock", "crypto", "portfolio"],
    "Travel":      ["trip", "travel", "itinerary", "vacation", "flight",
                    "hotel", "guide", "city-guide", "road-trip"],
    "Career":      ["resume", "interview", "career", "job", "hiring",
                    "promotion", "review", "salary"],
    "Education":   ["course", "lesson", "tutorial", "study", "learn",
                    "explainer", "primer", "notes", "syllabus"],
    "Personal":    ["family", "wedding", "birthday", "anniversary", "gift",
                    "party", "letter", "story"],
    "Housing":     ["apartment", "rent", "lease", "real-estate", "mortgage", "house"],
}

DEFAULTS = {
    "roots": [],
    "allow_repos": [],
    "max_depth": 3,
    "categories": {},          # merged on top of DEFAULT_CATEGORIES
    "enable_intent": False,    # LLM-derived intent metadata (requires ANTHROPIC_API_KEY)
    "intent_model": "claude-haiku-4-5",
    "intent_concurrency": 5,
    "drop_dir": None,          # where `artifold import <url>` saves fetched artifacts
}


def load() -> dict:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
    except Exception:
        cfg = {}
    return {**DEFAULTS, **cfg}


def save(cfg: dict) -> None:
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


def categories(cfg: dict | None = None) -> dict[str, list[str]]:
    cfg = cfg or load()
    return {**DEFAULT_CATEGORIES, **(cfg.get("categories") or {})}


def add_root(path: str | Path) -> tuple[bool, str]:
    """Add a root; returns (added?, resolved_path_str)."""
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        return False, f"not a directory: {p}"
    cfg = load()
    roots = list(cfg.get("roots") or [])
    s = str(p)
    if s in roots:
        return False, f"already configured: {s}"
    roots.append(s)
    cfg["roots"] = roots
    save(cfg)
    return True, s


def remove_root(path: str | Path) -> tuple[bool, str]:
    p = str(Path(path).expanduser().resolve())
    cfg = load()
    roots = list(cfg.get("roots") or [])
    if p not in roots:
        return False, f"not configured: {p}"
    roots.remove(p)
    cfg["roots"] = roots
    save(cfg)
    return True, p


def roots() -> list[Path]:
    return [Path(r) for r in (load().get("roots") or [])]
