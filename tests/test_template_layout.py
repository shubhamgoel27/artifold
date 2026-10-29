"""Guards for the dashboard's narrow-screen layout.

Both bugs here were silent: the page rendered, just cut off on a phone.
The old phone rule hid the sidebar, but it sat above the base `.sidebar`
rule, which has the same specificity and so won. And an unbounded grid
column let the top bar's minimum width (~520px) set the width of the
whole page.
"""
import re
from importlib import resources

CSS = resources.files("artifold").joinpath("template.html").read_text(encoding="utf-8")


def _rule(selector: str) -> str:
    m = re.search(r"^" + re.escape(selector) + r" \{(.*?)\}", CSS, re.S | re.M)
    assert m, f"no top-level rule for {selector}"
    return m.group(1)


def test_page_grid_column_cannot_grow_past_the_screen():
    assert "grid-template-columns: minmax(0, 1fr)" in _rule(".app")


def test_narrow_rules_come_after_the_base_rules_they_override():
    base = re.search(r"^\.sidebar \{", CSS, re.M).start()
    narrow = [m.start() for m in re.finditer(r"@media \(max-width: 760px\)", CSS)
              if ".sidebar" in CSS[m.start():m.start() + 600]]
    assert narrow, "no narrow-screen rule for the sidebar"
    assert all(n > base for n in narrow)


def test_every_narrow_screen_control_exists():
    for el in ('id="btn-filters"', 'id="side-done"', 'id="side-scrim"',
               'class="brand-name"'):
        assert el in CSS, el
