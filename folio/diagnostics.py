"""Preflight checks for Folio.

`folio doctor` runs all of these and reports pass / fail / info per item,
plus the exact command to fix each issue. Also reused by other commands
(e.g. `folio share`) to give targeted setup hints before they fail.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import __version__, config
from .paths import BROWSERS, CACHE_DIR, CONFIG_FILE


@dataclass
class Check:
    name: str
    status: str          # "ok" | "fail" | "warn" | "info"
    message: str
    fix: str | None = None

    @property
    def glyph(self) -> str:
        return {"ok": "✓", "fail": "✗", "warn": "!", "info": "i"}[self.status]


def _install_hint(pkg_brew: str, pkg_apt: str | None = None,
                  url_fallback: str | None = None) -> str:
    sys_name = platform.system().lower()
    if sys_name == "darwin":
        if shutil.which("brew"):
            return f"brew install {pkg_brew}"
        return f"install Homebrew (https://brew.sh), then: brew install {pkg_brew}"
    if sys_name == "linux":
        if shutil.which("apt-get") and pkg_apt:
            return f"sudo apt-get install -y {pkg_apt}"
        if shutil.which("dnf") and pkg_apt:
            return f"sudo dnf install -y {pkg_apt}"
        return url_fallback or f"install {pkg_brew} from your package manager"
    if sys_name == "windows":
        return f"winget install {pkg_brew}  (or scoop install {pkg_brew})"
    return url_fallback or f"install {pkg_brew}"


# ---------- individual checks ----------

def check_version() -> Check:
    return Check("folio", "ok", f"installed (v{__version__})")


def check_roots() -> Check:
    rs = config.load().get("roots") or []
    if not rs:
        return Check("roots", "warn", "no roots configured",
                     fix="folio add ~/Downloads   (or wherever your AI artifacts land)")
    missing = [r for r in rs if not Path(r).is_dir()]
    if missing:
        return Check("roots", "warn",
                     f"{len(rs)} configured, {len(missing)} missing on disk: {missing[0]}",
                     fix=f"folio remove {missing[0]}")
    return Check("roots", "ok", f"{len(rs)} root(s) configured")


def check_config() -> Check:
    if not CONFIG_FILE.exists():
        return Check("config", "warn", "no config yet",
                     fix="folio init")
    return Check("config", "ok", str(CONFIG_FILE))


def check_cache() -> Check:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        test = CACHE_DIR / ".write-test"
        test.write_text("x"); test.unlink()
        return Check("cache", "ok", str(CACHE_DIR))
    except Exception as e:
        return Check("cache", "fail", f"can't write to {CACHE_DIR}: {e}")


def check_playwright() -> Check:
    try:
        import playwright   # noqa: F401
        return Check("playwright", "ok", "installed")
    except ImportError:
        return Check("playwright", "fail", "not installed",
                     fix="pip install playwright")


def check_chromium() -> Check:
    # Either Playwright's default location, or our cache override
    default = Path.home() / "Library/Caches/ms-playwright"
    if any(BROWSERS.glob("chromium*")) or (default.exists() and any(default.glob("chromium*"))):
        return Check("chromium", "ok", "installed (for screenshots)")
    return Check("chromium", "warn", "browser not installed yet",
                 fix="python -m playwright install chromium  "
                     "(or run `folio scan` once — it installs on demand)")


def check_gh() -> Check:
    if not shutil.which("gh"):
        return Check("gh CLI", "fail", "not installed (needed for `folio share`)",
                     fix=_install_hint("gh", "gh", "https://cli.github.com/"))
    try:
        out = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        ver = (out.stdout.splitlines() or [""])[0]
        return Check("gh CLI", "ok", ver)
    except Exception:
        return Check("gh CLI", "ok", "installed")


def check_gh_auth() -> Check:
    if not shutil.which("gh"):
        return Check("gh auth", "info", "skipped (gh not installed)")
    r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if r.returncode != 0:
        return Check("gh auth", "fail", "not authenticated",
                     fix="gh auth login")
    # extract the user line
    user = ""
    for line in (r.stderr + r.stdout).splitlines():
        if "Logged in" in line:
            user = line.strip(); break
    return Check("gh auth", "ok", user or "authenticated")


def check_anthropic_extra() -> Check:
    try:
        import anthropic   # noqa: F401
        return Check("intent extra", "ok", "anthropic SDK installed (intent inference available)")
    except ImportError:
        return Check("intent extra", "info",
                     "not installed (optional; only needed for AI intent inference)",
                     fix="pip install 'ai-folio[intent]'")


def check_anthropic_key() -> Check:
    cfg = config.load()
    enabled = bool(cfg.get("enable_intent"))
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not enabled and not has_key:
        return Check("intent", "info", "disabled (default)")
    if enabled and not has_key:
        return Check("intent", "warn",
                     "enabled in config but ANTHROPIC_API_KEY not set",
                     fix="export ANTHROPIC_API_KEY=sk-ant-…   (in your shell rc)")
    if has_key and not enabled:
        return Check("intent", "info",
                     "key set but feature disabled — turn on with: folio scan --intent")
    return Check("intent", "ok", "enabled + key set")


ALL_CHECKS = [
    check_version, check_config, check_cache, check_roots,
    check_playwright, check_chromium,
    check_gh, check_gh_auth,
    check_anthropic_extra, check_anthropic_key,
]


def run_all() -> list[Check]:
    return [c() for c in ALL_CHECKS]


def report(checks: list[Check]) -> tuple[int, int]:
    """Print colorized report. Returns (failures, warnings)."""
    colors = {"ok": "\033[32m", "fail": "\033[31m", "warn": "\033[33m", "info": "\033[2m"}
    reset = "\033[0m"
    use_color = os.isatty(1) and os.environ.get("NO_COLOR") is None
    fails = warns = 0
    width = max(len(c.name) for c in checks) + 2
    for c in checks:
        col = colors[c.status] if use_color else ""
        end = reset if use_color else ""
        print(f"  {col}{c.glyph}{end} {c.name:<{width}} {c.message}")
        if c.fix:
            print(f"      fix: {c.fix}")
        if c.status == "fail":  fails += 1
        if c.status == "warn":  warns += 1
    return fails, warns


# ---------- targeted helpers used by other commands ----------

def share_preflight() -> list[Check]:
    """The subset relevant to `folio share`. Caller surfaces only failures."""
    out = [check_gh(), check_gh_auth()]
    return [c for c in out if c.status in ("fail", "warn")]
