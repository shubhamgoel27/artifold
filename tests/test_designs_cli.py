"""Tests for `artifold designs` list mode — the contract /craft depends on.

`--axes --limit` exists because the full projection carries a palette and a
flag block per artifact. On a real library that was ~68 KB of JSON read into
context on every /craft invocation, growing with every artifact shipped,
purely to answer "what did the last few pages look like?".
"""
import json
from argparse import Namespace

import pytest

from artifold import cli, paths, provenance

AXIS_KEYS = {"id", "name", "scale", "layout_archetype", "design_mode",
             "voice_register", "signature_device", "conceit", "added_at"}


@pytest.fixture
def library(tmp_path, monkeypatch):
    """Three fingerprinted artifacts, newest first by added_at."""
    # _cmd_designs does `from .paths import DATA` at call time, so patching
    # the module attribute is enough to redirect it.
    monkeypatch.setattr(provenance, "STORE", tmp_path / "provenance.json")
    monkeypatch.setattr(paths, "DATA", tmp_path / "data.json")

    items, projects = {}, []
    for i, day in enumerate(("03", "02", "01")):
        sha = f"{i}" * 40
        items[sha] = {
            "added_at": f"2026-07-{day}T00:00:00+00:00",
            # Proportioned like a real fingerprint: extracted palettes run
            # 6 colours and the flag block is always five keys.
            "design": {"palette": ["#fdf8ec", "#dbe4ec", "#a3b6c8",
                                   "#f4ead6", "#f8efdc", "#23405c"],
                       "fonts": ["Playfair Display", "Karla"],
                       "themed": True, "gradient": True, "glass": False,
                       "animated": False, "shadowed": True},
            "design_mode": f"mode-{i}", "voice_register": f"voice-{i}",
            "layout_archetype": f"layout-{i}",
            "signature_device": f"device-{i}",
            "scale": "read", "conceit": f"conceit-{i}", "tool": "claude",
        }
        projects.append({"name": f"artifact {i}", "dir": ".",
                         "category": "Engineering",
                         "primary": {"sha1": sha, "path": f"/x/{i}.html"},
                         "versions": [{"sha1": sha, "path": f"/x/{i}.html",
                                       "version": 1}]})
    provenance._save_raw({"version": provenance.SCHEMA, "items": items})
    (tmp_path / "data.json").write_text(json.dumps({"projects": projects}))
    return tmp_path


def _run(capsys, **kw):
    args = Namespace(id=None, json=True, limit=0, axes=False,
                     template=False, css=False, skeleton=False)
    for k, v in kw.items():
        setattr(args, k, v)
    assert cli._cmd_designs(args) == 0
    return json.loads(capsys.readouterr().out)


def test_full_projection_carries_design_detail(library, capsys):
    rows = _run(capsys)
    assert len(rows) == 3
    assert "palette" in rows[0] and "flags" in rows[0]


def test_axes_projection_drops_palette_and_flags(library, capsys):
    rows = _run(capsys, axes=True)
    assert set(rows[0]) == AXIS_KEYS
    assert "palette" not in rows[0]


def test_axes_projection_is_substantially_smaller(library, capsys):
    full = len(json.dumps(_run(capsys)))
    axes = len(json.dumps(_run(capsys, axes=True)))
    assert axes < full / 2


def test_limit_takes_the_most_recent(library, capsys):
    rows = _run(capsys, limit=2)
    assert [r["name"] for r in rows] == ["artifact 0", "artifact 1"]


def test_limit_zero_means_all(library, capsys):
    assert len(_run(capsys, limit=0)) == 3


def test_limit_beyond_the_library_is_not_an_error(library, capsys):
    assert len(_run(capsys, limit=99)) == 3


def test_conceit_and_scale_reach_the_contract(library, capsys):
    row = _run(capsys, axes=True, limit=1)[0]
    assert row["conceit"] == "conceit-0"
    assert row["scale"] == "read"


def test_superseded_entries_are_excluded(library, capsys):
    raw = provenance._load_raw()
    raw["items"]["0" * 40]["superseded_by"] = "9" * 40
    provenance._save_raw(raw)
    assert [r["name"] for r in _run(capsys, axes=True)] == \
        ["artifact 1", "artifact 2"]
