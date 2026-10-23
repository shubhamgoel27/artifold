"""The credit line on shared pages: public copy only, once, and optional."""
from artifold import config, share

CRAFT = (b'<!doctype html><html><head><meta name="artifold:generator" '
         b'content="craft"></head><body><h1>Hi</h1></body></html>')
PLAIN = b'<html><body><h1>Hi</h1><script>x()</script></BODY></html>'


def test_craft_pages_say_made_with_craft():
    out = share.add_credit(CRAFT)
    assert b"Made with craft" in out
    assert out.index(share.CREDIT_MARK.encode()) < out.index(b"</body>")


def test_other_pages_say_shared_with_artifold():
    out = share.add_credit(PLAIN)
    assert b"Shared with Artifold" in out and b"Made with craft" not in out
    assert out.index(b"<script>") < out.index(share.CREDIT_MARK.encode())
    assert out.rstrip().endswith(b"</BODY></html>")


def test_credit_is_added_only_once():
    once = share.add_credit(CRAFT)
    assert share.add_credit(once) == once


def test_page_without_body_tag_still_gets_it():
    assert share.CREDIT_MARK.encode() in share.add_credit(b"<h1>bare</h1>")


def test_only_the_last_body_close_counts():
    """A '</body>' inside a script string must not swallow the credit."""
    html = b'<body><script>s="</body>"</script></body>'
    out = share.add_credit(html)
    assert out.index(share.CREDIT_MARK.encode()) > out.index(b"</script>")


def test_setting_defaults_on_and_can_be_turned_off(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "c.json")
    assert config.get("share_credit") is True
    config.set_("share_credit", "off")
    assert config.load()["share_credit"] is False


def test_older_craft_pages_are_recognized_by_their_design_tags():
    old = (b'<html><head><meta name="artifold:design-mode" '
           b'content="magazine-fashion"></head><body></body></html>')
    assert b"Made with craft" in share.add_credit(old)


def test_another_generator_with_design_tags_is_not_called_craft():
    other = (b'<html><head><meta name="artifold:generator" content="hallmark">'
             b'<meta name="artifold:design-mode" content="x"></head><body></body></html>')
    assert b"Shared with Artifold" in share.add_credit(other)
