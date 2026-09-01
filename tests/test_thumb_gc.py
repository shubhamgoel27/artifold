"""Tests for thumbnail garbage collection.

The cache key is sha1(path+mtime+size), so every edit writes a new
thumbnail and strands the old one. Nothing ever deleted them: a real
133-project library held 513 files, 380 of them orphans, and 32 MB of the
44 MB total.
"""
import json

import pytest

from artifold import paths, shoot


@pytest.fixture
def cache(tmp_path, monkeypatch):
    thumbs = tmp_path / "thumbs"
    thumbs.mkdir()
    monkeypatch.setattr(shoot, "THUMBS", thumbs)
    monkeypatch.setattr(shoot, "MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(paths, "THUMBS", thumbs)
    monkeypatch.setattr(paths, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(paths, "CONFIG_DIR", tmp_path / "cfg")
    return thumbs


def _thumb(cache, key, size=100):
    f = cache / f"{key}.jpg"
    f.write_bytes(b"x" * size)
    return f


def test_deletes_only_unreferenced_thumbnails(cache):
    _thumb(cache, "keep1")
    _thumb(cache, "keep2")
    _thumb(cache, "drop1", 500)
    _thumb(cache, "drop2", 500)
    projects = [{"id": "a", "thumb": "thumbs/keep1.jpg"},
                {"id": "b", "thumb": "thumbs/keep2.jpg"}]

    deleted, freed = shoot.gc_thumbs(projects)

    assert deleted == 2
    assert freed == 1000
    assert {f.name for f in cache.glob("*.jpg")} == {"keep1.jpg", "keep2.jpg"}


def test_projects_without_a_thumb_do_not_protect_anything(cache):
    _thumb(cache, "orphan")
    deleted, _ = shoot.gc_thumbs([{"id": "a", "thumb": None}])
    assert deleted == 1


def test_an_empty_library_clears_the_cache(cache):
    _thumb(cache, "a")
    _thumb(cache, "b")
    assert shoot.gc_thumbs([])[0] == 2


def test_gc_is_idempotent(cache):
    _thumb(cache, "keep")
    _thumb(cache, "drop")
    projects = [{"id": "a", "thumb": "thumbs/keep.jpg"}]
    assert shoot.gc_thumbs(projects)[0] == 1
    assert shoot.gc_thumbs(projects) == (0, 0)


def test_non_jpg_files_are_left_alone(cache):
    (cache / "notes.txt").write_text("hi")
    shoot.gc_thumbs([])
    assert (cache / "notes.txt").exists()


def test_manifest_rows_for_dead_projects_are_pruned(cache, tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({
        "live": {"path": "/x/a.html", "thumb": "thumbs/keep.jpg"},
        "dead": {"path": "/x/b.html", "thumb": "thumbs/gone.jpg"},
    }))
    _thumb(cache, "keep")
    shoot.gc_thumbs([{"id": "live", "thumb": "thumbs/keep.jpg"}])
    assert list(json.loads((tmp_path / "manifest.json").read_text())) == ["live"]


def test_a_corrupt_manifest_does_not_raise(cache, tmp_path):
    (tmp_path / "manifest.json").write_text("{not json")
    _thumb(cache, "orphan")
    assert shoot.gc_thumbs([])[0] == 1


def test_missing_manifest_does_not_raise(cache):
    _thumb(cache, "orphan")
    assert shoot.gc_thumbs([])[0] == 1
