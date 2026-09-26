"""Tests for the machine-cost work: fewer wakeups, fewer browser runs,
smaller thumbnails, no redundant install subprocess."""
import os
import time
from pathlib import Path

import pytest

from artifold import scan, shoot

CFG = {"max_depth": 3, "allow_repos": []}


# --- the watcher applies the scanner's rules ---------------------------------

@pytest.fixture
def root(tmp_path):
    (tmp_path / "proj").mkdir()
    (tmp_path / "cloned" / ".git").mkdir(parents=True)
    return tmp_path


def test_library_html_passes(root):
    assert scan.is_library_path(root / "proj" / "a.html", [root], CFG)
    assert scan.is_library_path(root / "top.html", [root], CFG)


def test_non_html_is_rejected(root):
    assert not scan.is_library_path(root / "proj" / "a.css", [root], CFG)


def test_depth_cap_matches_the_scanner(root):
    # max_depth 3: root/a/b/c.html is depth 3 (kept), one deeper is not
    assert scan.is_library_path(root / "a" / "b" / "c.html", [root], CFG)
    assert not scan.is_library_path(root / "a" / "b" / "c" / "d.html", [root], CFG)


def test_cloned_repo_is_rejected_unless_allowed(root):
    p = root / "cloned" / "docs.html"
    assert not scan.is_library_path(p, [root], CFG)
    assert scan.is_library_path(p, [root], {**CFG, "allow_repos": ["cloned"]})


def test_skip_dirs_are_rejected(root):
    assert not scan.is_library_path(root / "node_modules" / "x.html", [root], CFG)


def test_outside_every_root_is_rejected(root, tmp_path_factory):
    other = tmp_path_factory.mktemp("elsewhere")
    assert not scan.is_library_path(other / "x.html", [root], CFG)


def test_watcher_and_scanner_agree(root):
    """Every file the scanner indexes must pass the watcher, and vice versa."""
    for rel in ["top.html", "proj/a.html", "a/b/c.html", "a/b/c/d.html",
                "cloned/docs.html", "node_modules/x.html"]:
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("<html><title>t</title></html>")
    found = set()
    for p in scan._find_html(root.resolve(), CFG["max_depth"]):
        rel = p.relative_to(root.resolve())
        if not scan._in_skipped_repo(rel, root.resolve(), set()):
            found.add(p.resolve())
    passed = {p.resolve() for p in root.rglob("*.html")
              if scan.is_library_path(p.resolve(), [root.resolve()], CFG)}
    assert found == passed


# --- thumbnails wait for edits to settle ------------------------------------

@pytest.fixture
def cache(tmp_path, monkeypatch):
    thumbs = tmp_path / "thumbs"
    thumbs.mkdir()
    monkeypatch.setattr(shoot, "THUMBS", thumbs)
    monkeypatch.setattr(shoot, "MANIFEST", tmp_path / "manifest.json")
    return tmp_path


def _proj(path, pid="p"):
    return {"id": pid, "primary": {"path": str(path)}}


def _with_previous_thumb(cache, pid="p"):
    (cache / "thumbs" / "old.jpg").write_bytes(b"x")
    (cache / "manifest.json").write_text(
        '{"%s": {"path": "x", "thumb": "thumbs/old.jpg"}}' % pid)


def test_fresh_edit_keeps_the_previous_thumbnail(cache):
    f = cache / "a.html"
    f.write_text("<html>v2</html>")          # mtime = now
    _with_previous_thumb(cache)
    proj = _proj(f)
    todo, deferred = shoot.resolve_cached_thumbs([proj], settle=30)
    assert todo == [] and deferred == 1
    assert proj["thumb"] == "thumbs/old.jpg"   # stale, not blank


def test_quiet_edit_is_shot(cache):
    f = cache / "a.html"
    f.write_text("<html>v2</html>")
    old = time.time() - 120
    os.utime(f, (old, old))
    _with_previous_thumb(cache)
    todo, deferred = shoot.resolve_cached_thumbs([_proj(f)], settle=30)
    assert len(todo) == 1 and deferred == 0


def test_brand_new_artifact_is_shot_at_once(cache):
    """No previous thumbnail to fall back on, so never leave the card blank."""
    f = cache / "a.html"
    f.write_text("<html>new</html>")
    todo, deferred = shoot.resolve_cached_thumbs([_proj(f)], settle=30)
    assert len(todo) == 1 and deferred == 0


def test_settle_zero_shoots_everything(cache):
    """`artifold scan` is an explicit request: no deferral."""
    f = cache / "a.html"
    f.write_text("<html>v2</html>")
    _with_previous_thumb(cache)
    todo, deferred = shoot.resolve_cached_thumbs([_proj(f)])
    assert len(todo) == 1 and deferred == 0


def test_previous_thumb_that_was_deleted_is_not_trusted(cache):
    f = cache / "a.html"
    f.write_text("<html>v2</html>")
    (cache / "manifest.json").write_text('{"p": {"thumb": "thumbs/gone.jpg"}}')
    todo, deferred = shoot.resolve_cached_thumbs([_proj(f)], settle=30)
    assert len(todo) == 1 and deferred == 0


# --- thumbnail format ------------------------------------------------------

def test_key_changes_with_thumb_version(monkeypatch):
    a = shoot._key("/x.html", 1.0, 10)
    monkeypatch.setattr(shoot, "THUMB_V", shoot.THUMB_V + 1)
    assert shoot._key("/x.html", 1.0, 10) != a


def test_thumbnails_capture_at_half_scale():
    assert shoot.THUMB_SCALE == 0.5


# --- no install subprocess when the browser is already there ----------------

def test_installed_browser_skips_the_subprocess(tmp_path, monkeypatch):
    b = tmp_path / "browsers"
    (b / "chromium_headless_shell-1161").mkdir(parents=True)
    (b / "chromium_headless_shell-1161" / "chrome").write_text("")
    monkeypatch.setattr(shoot, "BROWSERS", b)
    called = []
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: called.append(1))
    assert shoot.ensure_chromium() is True
    assert called == []


def test_force_still_runs_the_installer(tmp_path, monkeypatch):
    b = tmp_path / "browsers"
    (b / "chromium_headless_shell-1161").mkdir(parents=True)
    (b / "chromium_headless_shell-1161" / "chrome").write_text("")
    monkeypatch.setattr(shoot, "BROWSERS", b)
    import subprocess

    class R:
        returncode = 0
        stderr = ""
    called = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (called.append(1), R())[1])
    assert shoot.ensure_chromium(force=True) is True
    assert called == [1]


def test_empty_browser_dir_runs_the_installer(tmp_path, monkeypatch):
    monkeypatch.setattr(shoot, "BROWSERS", tmp_path / "browsers")
    import subprocess

    class R:
        returncode = 0
        stderr = ""
    called = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (called.append(1), R())[1])
    shoot.ensure_chromium()
    assert called == [1]


# --- steady-state scans don't re-read unchanged files ----------------------

from artifold import config, detect, provenance


def _reference_categorize(fields, cats):
    """The pre-optimisation implementation, kept as an oracle."""
    toks = {f: scan.WORD_RE.findall((fields.get(f) or "").lower())
            for f in scan.FIELD_WEIGHTS}
    scores = {}
    for cat, kws in cats.items():
        total = 0.0
        for kw in kws:
            kt = scan.WORD_RE.findall(kw.lower())
            if not kt:
                continue
            w = scan._kw_weight(kt)
            for field, fw in scan.FIELD_WEIGHTS.items():
                hits = scan._occurrences(toks[field], kt)
                if hits:
                    total += w * fw * (1 + 0.5 * min(hits - 1, 3))
        if total:
            scores[cat] = total
    if not scores:
        return "Other"
    best = max(scores.values())
    return next(c for c in cats if scores.get(c) == best)


def test_fast_categorizer_matches_the_reference_exactly():
    import random
    rng = random.Random(7)
    cats = config.DEFAULT_CATEGORIES
    vocab = [w for kws in cats.values() for kw in kws for w in kw.split()]
    vocab += ["the", "a", "report", "plan", "card", "wait", "ctrl", "html"]
    for _ in range(300):
        fields = {f: " ".join(rng.choice(vocab) for _ in range(rng.randint(0, 14)))
                  for f in scan.FIELD_WEIGHTS}
        assert scan._categorize(fields, cats) == _reference_categorize(fields, cats)


def _page(p, body="x"):
    p.write_text(f'<html><head><title>T</title>'
                 f'<meta name="artifold:intent" content="{body}"></head>'
                 f'<body><h1>T</h1></body></html>')


def test_unchanged_file_is_neither_hashed_nor_read_again(tmp_path, monkeypatch):
    f = tmp_path / "a.html"
    _page(f)
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    scan._scan_root(tmp_path, cfg, cats, {})
    hashed, read = [], []
    real_sha, real_meta = provenance.sha1_of, detect.extract_embedded_meta
    monkeypatch.setattr(provenance, "sha1_of", lambda p: (hashed.append(1), real_sha(p))[1])
    monkeypatch.setattr(detect, "extract_embedded_meta",
                        lambda h: (read.append(1), real_meta(h))[1])
    scan._scan_root(tmp_path, cfg, cats, {})
    assert hashed == [] and read == []


def test_edited_file_is_hashed_and_read_again(tmp_path):
    f = tmp_path / "a.html"
    _page(f, "first")
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    scan._scan_root(tmp_path, cfg, cats, {})
    _page(f, "second intent")
    proj = scan._scan_root(tmp_path, cfg, cats, {})[0]
    assert proj["primary"]["provenance"]["intent"] == "second intent"


def test_bumping_enrich_version_rereads_everything(tmp_path, monkeypatch):
    f = tmp_path / "a.html"
    _page(f)
    cfg, cats = {"allow_repos": [], "max_depth": 3}, {}
    scan._scan_root(tmp_path, cfg, cats, {})
    read = []
    real = detect.extract_embedded_meta
    monkeypatch.setattr(detect, "extract_embedded_meta",
                        lambda h: (read.append(1), real(h))[1])
    monkeypatch.setattr(scan, "ENRICH_V", scan.ENRICH_V + 1)
    scan._scan_root(tmp_path, cfg, cats, {})
    assert read == [1]


def test_hash_cache_survives_a_restart(tmp_path, monkeypatch):
    f = tmp_path / "a.html"
    _page(f)
    provenance.sha1_cached(f)
    provenance.flush_sha_cache()
    monkeypatch.setattr(provenance, "_SHA_CACHE", None)     # new process
    called = []
    monkeypatch.setattr(provenance, "sha1_of", lambda p: called.append(1))
    provenance.sha1_cached(f)
    assert called == []


def test_hash_cache_prunes_deleted_files(tmp_path):
    f = tmp_path / "a.html"
    _page(f)
    provenance.sha1_cached(f)
    f.unlink()
    provenance.flush_sha_cache(prune_missing=True)
    assert str(f) not in provenance._sha_cache()


def test_gc_does_not_rewrite_an_unchanged_store(tmp_path, monkeypatch):
    provenance.set_("a" * 40, path=str(tmp_path / "x"), tool="claude")
    provenance.gc({"a" * 40})
    writes = []
    monkeypatch.setattr(provenance, "_write_now", lambda d: writes.append(1))
    provenance.gc({"a" * 40})
    assert writes == []
