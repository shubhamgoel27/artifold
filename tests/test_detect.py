"""Tests for embedded artifold:* meta-tag extraction.

`conceit` and `scale` are the regression here: /craft emitted both for
months while detect.py parsed neither, so the dashboard never saw a conceit
and the skill's "intensity rotates too" rule had nothing to read.
"""
from artifold import detect

PAGE = """<!doctype html><html><head>
<meta name="artifold:intent" content="Six-day road trip itinerary">
<meta name="artifold:tool" content="claude">
<meta name="artifold:prompt" content="Revamp the itinerary">
<meta name="artifold:conceit" content="Six postcards written home early">
<meta name="artifold:scale" content="read">
<meta name="artifold:layout-archetype" content="card-stack-dossier">
<meta name="artifold:design-mode" content="postcard-from">
<meta name="artifold:voice-register" content="enthusiast">
<meta name="artifold:signature-device" content="hand-built route ribbon">
</head><body>hi</body></html>"""


def test_extracts_every_axis_including_conceit_and_scale():
    m = detect.extract_embedded_meta(PAGE)
    assert m["conceit"] == "Six postcards written home early"
    assert m["scale"] == "read"
    assert m["layout_archetype"] == "card-stack-dossier"
    assert m["design_mode"] == "postcard-from"
    assert m["voice_register"] == "enthusiast"
    assert m["signature_device"] == "hand-built route ribbon"
    assert m["intent"] == "Six-day road trip itinerary"
    assert m["tool"] == "claude"


def test_legacy_folio_prefix_still_parses():
    page = '<head><meta name="folio:conceit" content="an old one"></head>'
    assert detect.extract_embedded_meta(page)["conceit"] == "an old one"


def test_single_quotes_and_odd_spacing():
    page = "<head><meta   name='artifold:scale'   content='glance'></head>"
    assert detect.extract_embedded_meta(page)["scale"] == "glance"


def test_absent_tags_are_omitted_not_none():
    m = detect.extract_embedded_meta("<head><title>x</title></head>")
    assert m == {}


def test_tags_below_the_head_window_are_ignored():
    page = "<head>" + " " * 9000 + \
        '<meta name="artifold:scale" content="read"></head>'
    assert "scale" not in detect.extract_embedded_meta(page)


def test_detect_tool_from_markers():
    assert detect.detect_tool("see claude.ai/artifacts/abc") == "claude"
    assert detect.detect_tool("built with v0") == "v0"
    assert detect.detect_tool("<p>just some writing</p>") is None
