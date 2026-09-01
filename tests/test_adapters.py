"""Tests for reading provenance left by other design skills.

Fixtures follow the formats documented in Nutlope/hallmark's SKILL.md:
a CSS stamp on the first non-empty line, and a `.hallmark/log.json` at the
project root holding the last 20 runs, newest first.

These are somebody else's formats and they will drift. Every adapter must
fail soft — a stamp it no longer understands yields no metadata, never an
exception.
"""
import json

import pytest

from artifold import adapters, detect

STAMP = """/* Hallmark · macrostructure: Marquee Hero · tone: warm-editorial
   · anchor hue: oklch(0.72 0.14 45) · nav: N5 Floating pill
   · footer: Ft5 Statement · theme: Bloom */"""


def page(stamp=STAMP, body="<h1>Coffeebox</h1>"):
    return f"<!doctype html><html><head><style>\n{stamp}\n" \
           f":root{{--paper:#fdfaf5}}</style></head><body>{body}</body></html>"


@pytest.fixture
def project(tmp_path):
    (tmp_path / ".hallmark").mkdir()
    (tmp_path / ".hallmark" / "log.json").write_text(json.dumps([
        {"date": "2026-09-01", "macrostructure": "Marquee Hero",
         "theme": "Bloom", "enrichment": "E3", "brief": "Roaster landing page"},
        {"date": "2026-08-28", "macrostructure": "Long Document",
         "theme": "Almanac", "enrichment": "none", "brief": "Changelog"},
    ]))
    pages = tmp_path / "pages"
    pages.mkdir()
    f = pages / "roaster.html"
    f.write_text(page())
    return f


# --- the happy path --------------------------------------------------------

def test_maps_hallmark_vocabulary_onto_artifold_fields(project):
    got = adapters.extract(project.read_text(), project)
    assert got["generator"] == "hallmark"
    assert got["layout_archetype"] == "Marquee Hero"
    assert got["design_mode"] == "Bloom"
    assert got["voice_register"] == "warm-editorial"


def test_brief_from_the_log_becomes_intent(project):
    assert adapters.extract(project.read_text(), project)["intent"] \
        == "Roaster landing page"


def test_raw_values_are_kept_because_the_mapping_is_lossy(project):
    native = adapters.extract(project.read_text(), project)["generator_native"]
    assert native["anchor hue"] == "oklch(0.72 0.14 45)"
    assert native["nav"] == "N5 Floating pill"
    assert native["footer"] == "Ft5 Statement"
    assert native["log.enrichment"] == "E3"


def test_log_is_found_from_a_nested_directory(tmp_path):
    (tmp_path / ".hallmark").mkdir()
    (tmp_path / ".hallmark" / "log.json").write_text(json.dumps(
        [{"brief": "Deep page", "macrostructure": "Long Document"}]))
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    f = deep / "p.html"
    f.write_text(page())
    assert adapters.extract(f.read_text(), f)["intent"] == "Deep page"


def test_single_line_stamp_parses(tmp_path):
    f = tmp_path / "p.html"
    f.write_text(page("/* Hallmark · macrostructure: Split Rail · theme: Hum */"))
    got = adapters.extract(f.read_text(), f)
    assert got["layout_archetype"] == "Split Rail"
    assert got["design_mode"] == "Hum"


# --- no false positives ----------------------------------------------------

def test_a_page_with_no_stamp_is_not_claimed(tmp_path):
    f = tmp_path / "p.html"
    f.write_text("<html><head><style>body{color:red}</style></head></html>")
    assert adapters.extract(f.read_text(), f) == {}


def test_the_word_hallmark_in_prose_is_not_a_stamp(tmp_path):
    f = tmp_path / "p.html"
    f.write_text("<html><body><p>A hallmark of good design is restraint.</p></body></html>")
    assert adapters.extract(f.read_text(), f) == {}


def test_stamp_without_a_log_still_yields_the_axes(tmp_path):
    f = tmp_path / "p.html"
    f.write_text(page())
    got = adapters.extract(f.read_text(), f)
    assert got["layout_archetype"] == "Marquee Hero"
    assert "intent" not in got          # the brief lives only in the log


# --- failing soft ----------------------------------------------------------

def test_corrupt_log_does_not_raise(tmp_path):
    (tmp_path / ".hallmark").mkdir()
    (tmp_path / ".hallmark" / "log.json").write_text("{not json")
    f = tmp_path / "p.html"
    f.write_text(page())
    assert adapters.extract(f.read_text(), f)["layout_archetype"] == "Marquee Hero"


def test_empty_log_does_not_raise(tmp_path):
    (tmp_path / ".hallmark").mkdir()
    (tmp_path / ".hallmark" / "log.json").write_text("[]")
    f = tmp_path / "p.html"
    f.write_text(page())
    assert "intent" not in adapters.extract(f.read_text(), f)


def test_unrecognised_stamp_shape_yields_nothing_not_an_error(tmp_path):
    f = tmp_path / "p.html"
    f.write_text(page("/* Hallmark v9 :: totally new format, no pairs */"))
    assert adapters.extract(f.read_text(), f) == {}


def test_a_throwing_adapter_is_skipped(tmp_path, monkeypatch):
    def boom(html, path):
        raise RuntimeError("their format changed")
    monkeypatch.setattr(adapters, "ADAPTERS", [("boom", boom)])
    f = tmp_path / "p.html"
    f.write_text(page())
    assert adapters.extract(f.read_text(), f) == {}


# --- the contract ----------------------------------------------------------

def test_generator_tag_is_read_from_the_metadata_contract():
    html = '<head><meta name="artifold:generator" content="hallmark"></head>'
    assert detect.extract_embedded_meta(html)["generator"] == "hallmark"


def test_native_tags_outrank_an_adapter(tmp_path):
    """A skill that states its intent beats one inferred from a stamp."""
    from artifold import provenance, scan
    monkeyed = tmp_path / "prov.json"
    provenance.STORE = monkeyed
    (tmp_path / ".hallmark").mkdir()
    (tmp_path / ".hallmark" / "log.json").write_text(json.dumps(
        [{"brief": "from the log", "macrostructure": "Long Document"}]))
    f = tmp_path / "p.html"
    f.write_text(page().replace(
        "<head>",
        '<head><meta name="artifold:intent" content="stated outright">'
        '<meta name="artifold:layout-archetype" content="timeline-spine">'))

    projects = scan._scan_root(tmp_path, {"allow_repos": [], "max_depth": 3},
                               {}, {})
    prov = projects[0]["primary"]["provenance"]
    assert prov["intent"] == "stated outright"
    assert prov["layout_archetype"] == "timeline-spine"
    assert prov["generator"] == "hallmark"     # adapter still fills the gap
