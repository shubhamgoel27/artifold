"""Tests for in-place edit history, usage counting, and the store memo.

Background (tasks/v0.9-core-experience.md): a real library had 128
superseded provenance entries recording edits the dashboard never showed —
and every one of them was stamped for deletion 30 days out, so the history
was being collected before anything could read it.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

from artifold import provenance


def _mk(tmp_path, name="a.html", body="<html>one</html>"):
    f = tmp_path / name
    f.write_text(body)
    return f


def _sha(f):
    return provenance.sha1_of(f)


def _edit(f, body):
    """Change the file's content and carry provenance to the new hash."""
    f.write_text(body)
    return provenance.carry_forward(_sha(f), f)


# --- revision stamps -------------------------------------------------------

def test_carry_forward_stamps_both_ends(tmp_path):
    f = _mk(tmp_path)
    old = _sha(f)
    provenance.set_(old, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    new = _sha(f)

    assert provenance.get(new)["revised_at"]
    assert provenance.get(old)["superseded_at"]
    assert provenance.get(old)["superseded_by"] == new


def test_added_at_survives_an_edit(tmp_path):
    """A revision is not a new artifact. Creation time must not move."""
    f = _mk(tmp_path)
    old = _sha(f)
    provenance.set_(old, tool="claude", path=str(f))
    born = provenance.get(old)["added_at"]
    _edit(f, "<html>two</html>")
    assert provenance.get(_sha(f))["added_at"] == born


def test_usage_counts_survive_an_edit(tmp_path):
    f = _mk(tmp_path)
    provenance.set_(_sha(f), tool="claude", path=str(f))
    provenance.record_open(_sha(f))
    _edit(f, "<html>two</html>")
    assert provenance.get(_sha(f))["open_count"] == 1


# --- chain_for -------------------------------------------------------------

def test_chain_is_oldest_first_and_includes_the_live_head(tmp_path):
    f = _mk(tmp_path)
    first = _sha(f)
    provenance.set_(first, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    second = _sha(f)
    _edit(f, "<html>three</html>")
    third = _sha(f)

    chain = provenance.chain_for(third)
    assert [c["sha1"] for c in chain] == [first, second, third]


def test_chain_of_an_unedited_artifact_is_one(tmp_path):
    f = _mk(tmp_path)
    provenance.set_(_sha(f), tool="claude", path=str(f))
    assert len(provenance.chain_for(_sha(f))) == 1


def test_chain_of_an_unknown_sha_is_empty():
    assert provenance.chain_for("f" * 40) == []


def test_chain_survives_a_cycle(tmp_path):
    """A corrupt store must not hang the scan."""
    a, b = "a" * 40, "b" * 40
    provenance._save_raw({"version": provenance.SCHEMA, "items": {
        a: {"previous_sha": b}, b: {"previous_sha": a}}})
    assert len(provenance.chain_for(a)) == 2


# --- gc keeps history ------------------------------------------------------

def test_gc_does_not_orphan_revisions_of_a_live_artifact(tmp_path):
    f = _mk(tmp_path)
    first = _sha(f)
    provenance.set_(first, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    _edit(f, "<html>three</html>")
    live = _sha(f)

    provenance.gc({live})
    assert "orphaned_at" not in provenance.get(first)


def test_gc_still_orphans_history_of_a_deleted_artifact(tmp_path):
    f = _mk(tmp_path)
    first = _sha(f)
    provenance.set_(first, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    dead = _sha(f)
    f.unlink()

    provenance.gc(set())          # nothing is live any more
    assert provenance.get(first)["orphaned_at"]
    assert provenance.get(dead)["orphaned_at"]


def test_gc_deletes_orphans_past_the_ttl_but_keeps_live_history(tmp_path):
    f = _mk(tmp_path)
    first = _sha(f)
    provenance.set_(first, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    live = _sha(f)

    stale = (datetime.now(timezone.utc)
             - timedelta(days=provenance.ORPHAN_TTL_DAYS + 1)).isoformat()
    raw = provenance._load_raw()
    raw["items"]["dead" + "0" * 36] = {"orphaned_at": stale}
    provenance._save_raw(raw)

    deleted = provenance.gc({live})
    assert deleted == 1
    assert provenance.get(first) is not None      # history untouched


def test_gc_reunorphans_history_after_it_was_marked(tmp_path):
    """Upgrade path: chains stamped by an older version must recover."""
    f = _mk(tmp_path)
    first = _sha(f)
    provenance.set_(first, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    live = _sha(f)

    raw = provenance._load_raw()
    raw["items"][first]["orphaned_at"] = datetime.now(timezone.utc).isoformat()
    provenance._save_raw(raw)

    provenance.gc({live})
    assert "orphaned_at" not in provenance.get(first)


# --- opens -----------------------------------------------------------------

def test_record_open_counts_and_stamps(tmp_path):
    f = _mk(tmp_path)
    sha = _sha(f)
    provenance.set_(sha, tool="claude", path=str(f))
    for _ in range(3):
        provenance.record_open(sha)
    e = provenance.get(sha)
    assert e["open_count"] == 3
    assert e["last_opened_at"]


def test_record_open_on_an_unknown_sha_is_a_no_op():
    assert provenance.record_open("0" * 40) is None


def test_sha_for_path_finds_the_live_entry(tmp_path):
    f = _mk(tmp_path)
    sha = _sha(f)
    provenance.set_(sha, tool="claude", path=str(f))
    assert provenance.sha_for_path(str(f)) == sha


def test_sha_for_path_ignores_superseded_entries(tmp_path):
    f = _mk(tmp_path)
    old = _sha(f)
    provenance.set_(old, tool="claude", path=str(f))
    _edit(f, "<html>two</html>")
    assert provenance.sha_for_path(str(f)) == _sha(f)


def test_sha_for_path_resolves_symlinks(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    f = _mk(real)
    provenance.set_(_sha(f), tool="claude", path=str(f))
    link = tmp_path / "link"
    link.symlink_to(real)
    assert provenance.sha_for_path(link / "a.html") == _sha(f)


def test_sha_for_path_of_an_unknown_file_is_none(tmp_path):
    assert provenance.sha_for_path(tmp_path / "nope.html") is None


# --- store memo ------------------------------------------------------------

def test_memo_serves_repeat_reads_without_reparsing(tmp_path, monkeypatch):
    f = _mk(tmp_path)
    provenance.set_(_sha(f), tool="claude", path=str(f))
    calls = []
    real = provenance.STORE.read_text
    monkeypatch.setattr(type(provenance.STORE), "read_text",
                        lambda self, *a, **k: (calls.append(1), real())[1])
    for _ in range(20):
        provenance.all_items()
    assert calls == []          # all served from the memo


def test_memo_notices_a_write_from_another_process(tmp_path):
    f = _mk(tmp_path)
    sha = _sha(f)
    provenance.set_(sha, tool="claude", path=str(f))
    assert provenance.get(sha)["tool"] == "claude"

    raw = json.loads(provenance.STORE.read_text())
    raw["items"][sha]["tool"] = "gemini"
    # Bypass _save_raw entirely, the way a second process would.
    provenance.STORE.write_text(json.dumps(raw))
    assert provenance.get(sha)["tool"] == "gemini"


def test_memo_does_not_leak_between_two_stores(tmp_path, monkeypatch):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    monkeypatch.setattr(provenance, "STORE", a)
    provenance._save_raw({"version": provenance.SCHEMA,
                          "items": {"1" * 40: {"tool": "claude"}}})
    monkeypatch.setattr(provenance, "STORE", b)
    provenance._save_raw({"version": provenance.SCHEMA,
                          "items": {"2" * 40: {"tool": "gemini"}}})
    monkeypatch.setattr(provenance, "STORE", a)
    assert list(provenance.all_items()) == ["1" * 40]


# --- what the dashboard actually reads -------------------------------------

def _page(p, title="Thing"):
    p.write_text(f"<html><head><title>{title}</title></head>"
                 f"<body><h1>{title}</h1></body></html>")


def test_scan_attaches_revision_and_usage_fields(tmp_path):
    """The card badges and the "Most used" sort read these four keys."""
    from artifold import scan
    f = tmp_path / "thing.html"
    _page(f, "Thing")
    projects = scan._scan_root(tmp_path, {"allow_repos": [], "max_depth": 3},
                               {}, {})
    proj = projects[0]
    assert proj["revision_count"] == 1        # created, never edited
    assert proj["revisions"][0]["sha1"] == provenance.sha1_of(f)
    assert proj["open_count"] == 0
    assert proj["last_opened_at"] is None


def test_scan_reports_an_edited_artifact_as_multi_revision(tmp_path):
    from artifold import scan
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    f = tmp_path / "thing.html"
    _page(f, "Thing")
    scan._scan_root(tmp_path, cfg, cats, {})       # records the first hash
    _page(f, "Thing revised")
    projects = scan._scan_root(tmp_path, cfg, cats, {})

    proj = projects[0]
    assert proj["revision_count"] == 2
    assert proj["revisions"][-1]["sha1"] == provenance.sha1_of(f)
    assert proj["revisions"][-1]["revised_at"]


def test_scan_surfaces_open_counts(tmp_path):
    from artifold import scan
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    f = tmp_path / "thing.html"
    _page(f, "Thing")
    scan._scan_root(tmp_path, cfg, cats, {})
    provenance.record_open(provenance.sha1_of(f))
    provenance.record_open(provenance.sha1_of(f))

    proj = scan._scan_root(tmp_path, cfg, cats, {})[0]
    assert proj["open_count"] == 2
    assert proj["last_opened_at"]
