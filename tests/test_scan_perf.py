"""Tests for the scan hot path.

A scan enriches every file, and every enrichment wrote the whole provenance
store back to disk: 273 serialisations of a 546 KB document in one scan,
which profiled at 75% of scan time. These tests pin the two fixes — batched
writes and a versioned fingerprint cache — because both are the kind of
optimisation that fails silently by dropping data rather than by crashing.
"""
import json

import pytest

from artifold import design, provenance, scan


def _writes(monkeypatch):
    """Count actual writes to the store."""
    n = []
    real = provenance._write_now
    monkeypatch.setattr(provenance, "_write_now",
                        lambda d: (n.append(1), real(d))[1])
    return n


# --- batched writes --------------------------------------------------------

def test_batch_collapses_many_writes_into_one(tmp_path, monkeypatch):
    n = _writes(monkeypatch)
    with provenance.batch():
        for i in range(50):
            provenance.set_(f"{i:040d}", tool="claude")
    assert len(n) == 1


def test_without_a_batch_every_write_hits_disk(tmp_path, monkeypatch):
    n = _writes(monkeypatch)
    for i in range(5):
        provenance.set_(f"{i:040d}", tool="claude")
    assert len(n) == 5


def test_reads_inside_a_batch_see_pending_writes(tmp_path):
    with provenance.batch():
        provenance.set_("a" * 40, tool="claude", intent="pending")
        assert provenance.get("a" * 40)["intent"] == "pending"


def test_the_batch_actually_lands_on_disk(tmp_path):
    with provenance.batch():
        provenance.set_("b" * 40, tool="claude", intent="durable")
    raw = json.loads(provenance.STORE.read_text())
    assert raw["items"]["b" * 40]["intent"] == "durable"


def test_batch_flushes_even_when_the_body_raises(tmp_path):
    with pytest.raises(ValueError):
        with provenance.batch():
            provenance.set_("c" * 40, tool="claude")
            raise ValueError("boom")
    raw = json.loads(provenance.STORE.read_text())
    assert "c" * 40 in raw["items"]


def test_nested_batches_flush_once_at_the_outermost_exit(tmp_path, monkeypatch):
    n = _writes(monkeypatch)
    with provenance.batch():
        provenance.set_("d" * 40, tool="claude")
        with provenance.batch():
            provenance.set_("e" * 40, tool="claude")
        assert len(n) == 0          # inner exit must not flush
    assert len(n) == 1


def test_a_batch_that_writes_nothing_writes_nothing(tmp_path, monkeypatch):
    n = _writes(monkeypatch)
    with provenance.batch():
        provenance.get("f" * 40)
    assert len(n) == 0


def test_carry_forward_survives_a_batch(tmp_path):
    f = tmp_path / "a.html"
    f.write_text("<html>one</html>")
    first = provenance.sha1_of(f)
    provenance.set_(first, tool="claude", path=str(f))
    with provenance.batch():
        f.write_text("<html>two</html>")
        provenance.carry_forward(provenance.sha1_of(f), f)
    raw = json.loads(provenance.STORE.read_text())
    assert raw["items"][first]["superseded_by"] == provenance.sha1_of(f)


# --- fingerprint cache -----------------------------------------------------

def _page(p, css="body{color:#123456}"):
    p.write_text(f"<html><head><title>T</title><style>{css}</style></head>"
                 f"<body><h1>T</h1></body></html>")


def test_fingerprint_is_computed_once_then_reused(tmp_path, monkeypatch):
    f = tmp_path / "a.html"
    _page(f)
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    calls = []
    real = design.extract
    monkeypatch.setattr(design, "extract",
                        lambda html: (calls.append(1), real(html))[1])

    scan._scan_root(tmp_path, cfg, cats, {})
    assert len(calls) == 1
    scan._scan_root(tmp_path, cfg, cats, {})
    assert len(calls) == 1          # unchanged bytes, no recompute


def test_edited_file_gets_a_fresh_fingerprint(tmp_path, monkeypatch):
    f = tmp_path / "a.html"
    _page(f)
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    scan._scan_root(tmp_path, cfg, cats, {})
    _page(f, "body{color:#abcdef}")
    projects = scan._scan_root(tmp_path, cfg, cats, {})
    palette = projects[0]["primary"]["provenance"]["design"]["palette"]
    assert "#abcdef" in palette


def test_bumping_the_schema_rebuilds_cached_fingerprints(tmp_path, monkeypatch):
    f = tmp_path / "a.html"
    _page(f)
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    scan._scan_root(tmp_path, cfg, cats, {})

    calls = []
    real = design.extract
    monkeypatch.setattr(design, "SCHEMA", design.SCHEMA + 1)
    monkeypatch.setattr(design, "extract",
                        lambda html: (calls.append(1), {**real(html),
                                                        "v": design.SCHEMA})[1])
    scan._scan_root(tmp_path, cfg, cats, {})
    assert len(calls) == 1          # stale schema forces a recompute


def test_every_fingerprint_carries_its_schema_version():
    assert design.extract("<style>body{color:red}</style>")["v"] == design.SCHEMA
