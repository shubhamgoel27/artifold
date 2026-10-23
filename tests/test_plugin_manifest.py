"""The Claude Code plugin must point at the bundled skill and track the package version."""
import json
from pathlib import Path

from artifold import __version__

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
MARKET = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())


def test_versions_match():
    assert PLUGIN["version"] == __version__


def test_skill_path_resolves_to_craft():
    dirs = [ROOT / p for p in PLUGIN["skills"]]
    assert any((d / "craft" / "SKILL.md").is_file() for d in dirs)


def test_marketplace_lists_this_plugin():
    names = [p["name"] for p in MARKET["plugins"]]
    assert PLUGIN["name"] in names
