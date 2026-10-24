"""Tests for hiding pages and folders from the dashboard.

Hiding must never touch a file. It has to survive the things that happen
to a page after it is hidden: a rename, an in-place edit, a new -v2, a new
file in a hidden folder. And it must refuse paths outside every root.
"""
import argparse
import json

import pytest

from artifold import build, cli, config, paths, provenance, scan, serve


def _write(p, title):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"<html><head><title>{title}</title></head>"
                 f"<body><h1>{title}</h1></body></html>")
    return p


@pytest.fixture
def lib(tmp_path, monkeypatch):
    """A root, a throwaway config and data.json, and no real server."""
    root = tmp_path / "root"
    root.mkdir()
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"roots": [str(root)]}))
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_file)
    data = tmp_path / "data.json"
    monkeypatch.setattr(paths, "DATA", data)
    monkeypatch.setattr(build, "DATA", data)
    monkeypatch.setattr(build, "INDEX", tmp_path / "index.html")
    monkeypatch.setattr(cli, "_refresh_library", lambda: rescan(root))
    return root


def rescan(root):
    cfg = config.load()
    projects = scan._scan_root(root, cfg, {}, {})
    build.build(projects, [str(root)])
    return projects


def by_name(projects, name):
    return next(p for p in projects if p["name"] == name)


def test_hiding_never_touches_the_file(lib):
    f = _write(lib / "notes.html", "Notes")
    before = f.read_bytes()
    provenance.set_hidden([f], True)
    assert f.read_bytes() == before
    assert by_name(rescan(lib), "Notes")["hidden"] == "self"


def test_unhide_clears_it(lib):
    f = _write(lib / "notes.html", "Notes")
    provenance.set_hidden([f], True)
    provenance.set_hidden([f], False)
    assert "hidden" not in by_name(rescan(lib), "Notes")


def test_hidden_survives_a_rename(lib):
    f = _write(lib / "notes.html", "Notes")
    provenance.set_hidden([f], True)
    f.rename(lib / "renamed.html")
    assert by_name(rescan(lib), "Notes")["hidden"] == "self"


def test_hidden_survives_an_in_place_edit(lib):
    f = _write(lib / "notes.html", "Notes")
    rescan(lib)
    provenance.set_hidden([f], True)
    _write(f, "Notes")
    f.write_text(f.read_text() + "<p>more</p>")
    assert by_name(rescan(lib), "Notes")["hidden"] == "self"


def test_a_new_version_of_a_hidden_page_stays_hidden(lib):
    f = _write(lib / "deck" / "deck.html", "Deck")
    provenance.set_hidden([f], True)
    _write(lib / "deck" / "deck-v2.html", "Deck")
    p = by_name(rescan(lib), "Deck")
    assert p["version_count"] == 2
    assert p["hidden"] == "self"


def test_hidden_folder_covers_files_added_later(lib):
    _write(lib / "exports" / "out.html", "Out")
    _write(lib / "keep" / "keep.html", "Keep")
    config.set_dir_hidden(lib / "exports", True)
    _write(lib / "exports" / "later.html", "Later")
    projects = rescan(lib)
    for name in ("Out", "Later"):
        p = by_name(projects, name)
        assert p["hidden"] == "folder"
        assert p["hidden_dir"] == str((lib / "exports").resolve())
    assert "hidden" not in by_name(projects, "Keep")


def test_category_counts_leave_out_hidden_pages(lib):
    a = _write(lib / "a.html", "Alpha")
    _write(lib / "b.html", "Beta")
    provenance.set_hidden([a], True)
    rescan(lib)
    d = json.loads(paths.DATA.read_text())
    assert sum(d["counts"].values()) == 1
    assert len(d["projects"]) == 2          # still there for the Hidden view


def test_server_refuses_paths_outside_every_root(lib, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "roots", lambda: [lib])
    outside = _write(tmp_path / "outside.html", "Outside")
    status, body = serve.hide_request({"paths": [str(outside)]})
    assert status == 403
    assert provenance.sha_for_path(outside) is None
    assert not provenance.all_items()


def test_server_refuses_a_folder_outside_every_root(lib, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "roots", lambda: [lib])
    status, _ = serve.hide_request({"dir": str(tmp_path)})
    assert status == 403
    assert config.hidden_dirs() == []


def test_server_needs_paths_or_dir(lib):
    assert serve.hide_request({})[0] == 400


def test_server_hides_and_unhides(lib, monkeypatch):
    monkeypatch.setattr(config, "roots", lambda: [lib])
    f = _write(lib / "notes.html", "Notes")
    assert serve.hide_request({"paths": [str(f)]}) == (200, {"changed": 1})
    assert by_name(rescan(lib), "Notes")["hidden"] == "self"
    assert serve.hide_request({"paths": [str(f)], "hidden": False})[0] == 200
    assert "hidden" not in by_name(rescan(lib), "Notes")


def test_cli_hide_takes_every_version_and_unhide_brings_it_back(lib, capsys):
    v1 = _write(lib / "deck" / "deck.html", "Deck")
    v2 = _write(lib / "deck" / "deck-v2.html", "Deck")
    rescan(lib)
    cli._cmd_hide(argparse.Namespace(paths=[str(v1)]))
    assert "1 other version" in capsys.readouterr().out
    assert by_name(json.loads(paths.DATA.read_text())["projects"],
                   "Deck")["hidden"] == "self"
    # Unhiding the other version alone must bring the whole page back.
    cli._cmd_hide(argparse.Namespace(paths=[str(v2)]), hidden=False)
    assert "hidden" not in by_name(
        json.loads(paths.DATA.read_text())["projects"], "Deck")


def test_search_skips_hidden_unless_all(lib, capsys):
    f = _write(lib / "coffee.html", "Coffee tier list")
    provenance.set_hidden([f], True)
    rescan(lib)
    capsys.readouterr()
    args = argparse.Namespace(query=["coffee"], json=True, limit=10, all=False)
    assert cli._cmd_search(args) == 1
    assert json.loads(capsys.readouterr().out) == []
    args.all = True
    assert cli._cmd_search(args) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1
