"""Tests for trashing artifacts.

The dashboard sends a whole project in one request. It used to send one
request per file, and each one kicked a full rescan of the library, so
deleting a 3-file project scanned everything three times.

`trash_file` is stubbed here: these tests are about routing, refusal and
partial failure, not about whether send2trash works.
"""
import pytest

from artifold import config, serve, trash


@pytest.fixture
def rooted(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "roots", lambda: [tmp_path])
    calls = []

    def fake_trash(p):
        calls.append(str(p))
        return True, str(p)

    monkeypatch.setattr(trash, "trash_file", fake_trash)

    def make(name):
        f = tmp_path / name
        f.write_text("<html></html>")
        return f

    return make, calls


def test_trashes_every_path_in_one_call(rooted):
    make, calls = rooted
    files = [make(f"a{i}.html") for i in range(3)]
    trashed, errors = serve._trash_paths([str(f) for f in files])
    assert len(trashed) == 3
    assert errors == []
    assert calls == [str(f) for f in files]


def test_refuses_a_path_outside_every_root(rooted, tmp_path):
    make, calls = rooted
    outside = tmp_path.parent / "elsewhere.html"
    outside.write_text("<html></html>")
    trashed, errors = serve._trash_paths([str(outside)])
    assert trashed == []
    assert "not under any configured root" in errors[0]["error"]
    assert calls == []                  # never reached the filesystem


def test_one_bad_path_does_not_strand_the_others(rooted, tmp_path):
    make, calls = rooted
    good = make("good.html")
    outside = tmp_path.parent / "bad.html"
    outside.write_text("<html></html>")

    trashed, errors = serve._trash_paths([str(outside), str(good)])
    assert trashed == [str(good)]
    assert len(errors) == 1


def test_a_failing_delete_is_reported_not_raised(rooted, monkeypatch):
    make, _ = rooted
    f = make("locked.html")
    monkeypatch.setattr(trash, "trash_file",
                        lambda p: (False, "permission denied"))
    trashed, errors = serve._trash_paths([str(f)])
    assert trashed == []
    assert errors[0]["error"] == "permission denied"


def test_missing_file_inside_a_root_is_refused_before_deleting(rooted, tmp_path):
    make, calls = rooted
    trashed, errors = serve._trash_paths([str(tmp_path / "ghost.html")])
    assert trashed == []
    assert calls == []


def test_empty_input_is_empty_output(rooted):
    assert serve._trash_paths([]) == ([], [])
