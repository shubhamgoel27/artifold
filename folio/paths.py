"""User-scoped config and cache locations.

Layout (mac):
    config:   ~/Library/Application Support/folio/config.json
    cache:    ~/Library/Caches/folio/
              ├── index.html
              ├── data.json
              ├── manifest.json
              ├── thumbs/<hash>.jpg
              └── browsers/  (Playwright chromium, isolated to folio)

Linux uses XDG defaults (~/.config/folio, ~/.cache/folio).
"""
from __future__ import annotations

from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir

APP = "folio"

CONFIG_DIR = Path(user_config_dir(APP))
CONFIG_FILE = CONFIG_DIR / "config.json"

CACHE_DIR = Path(user_cache_dir(APP))
THUMBS = CACHE_DIR / "thumbs"
MANIFEST = CACHE_DIR / "manifest.json"
DATA = CACHE_DIR / "data.json"
INDEX = CACHE_DIR / "index.html"
BROWSERS = CACHE_DIR / "browsers"


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS.mkdir(parents=True, exist_ok=True)
