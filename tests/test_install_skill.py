"""craft installs for every agent found, and only once."""
import argparse

import pytest

from artifold import cli


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    monkeypatch.setattr("shutil.which", lambda _: None)
    return tmp_path


def run(agent="auto", force=False):
    return cli._cmd_install_skill(
        argparse.Namespace(dest=None, force=force, agent=agent))


def test_no_agent_found_falls_back_to_claude_code(home):
    assert run() == 0
    assert (home / ".claude/skills/craft/SKILL.md").exists()
    assert not (home / ".agents").exists()


def test_codex_gets_its_own_copy(home):
    (home / ".codex").mkdir()
    assert run() == 0
    assert (home / ".agents/skills/craft/SKILL.md").exists()
    assert (home / ".agents/skills/craft/references/layouts.md").exists()


def test_all_installs_both(home):
    run("all")
    assert cli._skill_installed("claude") and cli._skill_installed("codex")


def test_existing_install_is_kept_unless_forced(home):
    run("claude")
    (home / ".claude/skills/craft/SKILL.md").write_text("mine")
    assert run("claude") == 1
    assert (home / ".claude/skills/craft/SKILL.md").read_text() == "mine"
    assert run("claude", force=True) == 0
    assert "mine" != (home / ".claude/skills/craft/SKILL.md").read_text()


def test_wizard_offers_only_what_is_missing(home, monkeypatch):
    (home / ".claude").mkdir()
    (home / ".codex").mkdir()
    run("claude")
    asked = []
    monkeypatch.setattr("builtins.input", lambda p: asked.append(p) or "")
    cli._wizard_offer_skill()
    assert "Codex" in asked[0] and "Claude" not in asked[0]
    assert cli._skill_installed("codex")
    asked.clear()
    cli._wizard_offer_skill()
    assert asked == []


def test_a_plugin_install_counts_as_installed(home, monkeypatch):
    (home / ".claude/plugins/cache/artifold/craft/0.15.0").mkdir(parents=True)
    asked = []
    monkeypatch.setattr("builtins.input", lambda p: asked.append(p) or "")
    cli._wizard_offer_skill()
    assert asked == []
