"""Tests for counting opens on the server side.

An open is the only moment Artifold learns that an artifact is *used*
rather than merely made. It must count real opens, refuse anything outside
a configured root, and never raise into the request handler.
"""
from pathlib import Path

import pytest

from artifold import config, provenance, serve


@pytest.fixture
def rooted(tmp_path, monkeypatch):
    monkeypatch.setattr(provenance, "STORE", tmp_path / "provenance.json")
    monkeypatch.setattr(config, "roots", lambda: [tmp_path])
    f = tmp_path / "thing.html"
    f.write_text("<html>hi</html>")
    sha = provenance.sha1_of(f)
    provenance.set_(sha, tool="claude", path=str(f))
    return f, sha


def test_counts_an_open_inside_a_root(rooted):
    f, sha = rooted
    assert serve._count_open(f) is True
    assert provenance.get(sha)["open_count"] == 1


def test_repeat_opens_accumulate(rooted):
    f, sha = rooted
    for _ in range(4):
        serve._count_open(f)
    assert provenance.get(sha)["open_count"] == 4


def test_refuses_a_path_outside_every_root(rooted, tmp_path):
    outside = tmp_path.parent / "outside.html"
    outside.write_text("<html>no</html>")
    assert serve._count_open(outside) is False


def test_refuses_a_file_that_does_not_exist(rooted, tmp_path):
    assert serve._count_open(tmp_path / "ghost.html") is False


def test_untracked_file_inside_a_root_is_not_counted(rooted, tmp_path):
    stranger = tmp_path / "stranger.html"
    stranger.write_text("<html>unknown</html>")
    assert serve._count_open(stranger) is False


def test_never_raises(rooted, monkeypatch):
    f, _ = rooted
    monkeypatch.setattr(provenance, "record_open",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError))
    assert serve._count_open(f) is False


def test_empty_path_is_refused(rooted):
    assert serve._count_open(Path("")) is False
