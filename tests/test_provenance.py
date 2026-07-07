"""Tests for provenance carry-forward (in-place edits) and orphan GC."""
from datetime import datetime, timedelta, timezone

from artifold import provenance


def test_carry_forward_migrates_entry_on_edit(tmp_path):
    f = tmp_path / "report.html"
    f.write_text("<html>v1</html>")
    old_sha = provenance.sha1_of(f)
    provenance.set_(old_sha, tool="claude", prompt="make a report",
                    tags=["ml"], path=str(f))

    f.write_text("<html>v2, edited in place</html>")
    new_sha = provenance.sha1_of(f)
    assert new_sha != old_sha

    entry = provenance.carry_forward(new_sha, f)
    assert entry is not None
    assert entry["tool"] == "claude"
    assert entry["prompt"] == "make a report"
    assert entry["previous_sha"] == old_sha
    assert provenance.get(old_sha)["superseded_by"] == new_sha
    # second call is a no-op returning the existing entry
    assert provenance.carry_forward(new_sha, f)["previous_sha"] == old_sha


def test_carry_forward_without_history_returns_none(tmp_path):
    f = tmp_path / "fresh.html"
    f.write_text("<html>new</html>")
    assert provenance.carry_forward(provenance.sha1_of(f), f) is None


def test_gc_stamps_then_deletes_orphans():
    provenance.set_("a" * 40, tool="claude")
    provenance.gc(active_shas=set())
    assert provenance.get("a" * 40).get("orphaned_at")

    # young orphan survives
    assert provenance.gc(active_shas=set()) == 0
    assert provenance.get("a" * 40)

    # age the stamp past the TTL → deleted
    old = datetime.now(timezone.utc) - timedelta(
        days=provenance.ORPHAN_TTL_DAYS + 1)
    provenance.set_("a" * 40, orphaned_at=old.isoformat(timespec="seconds"))
    assert provenance.gc(active_shas=set()) == 1
    assert provenance.get("a" * 40) is None


def test_gc_unorphans_reseen_and_spares_live_paths(tmp_path):
    provenance.set_("b" * 40, tool="claude")
    provenance.gc(active_shas=set())
    assert provenance.get("b" * 40).get("orphaned_at")
    provenance.gc(active_shas={"b" * 40})
    assert "orphaned_at" not in provenance.get("b" * 40)

    # entry with a live path (variant / depth-excluded file) is never stamped
    f = tmp_path / "variant-print.html"
    f.write_text("<html></html>")
    provenance.set_("c" * 40, tool="claude", path=str(f))
    provenance.gc(active_shas=set())
    assert "orphaned_at" not in provenance.get("c" * 40)
