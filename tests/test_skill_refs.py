"""The bundled /craft skill must be internally consistent.

SKILL.md points into references/*.md by file name, by recipe section (§N),
and the references point back by "SKILL.md section N". A stale copy of
SKILL.md once shipped over newer references, and nothing noticed: the skill
kept citing sections that had moved and never read three whole catalogs.
These tests make that kind of drift fail loudly.
"""
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent / "artifold" / "skills" / "craft"
SKILL = SKILL_DIR / "SKILL.md"
REFS = SKILL_DIR / "references"


def _all_docs():
    return [SKILL, *sorted(REFS.glob("*.md"))]


def test_every_mentioned_reference_file_exists():
    missing = []
    for doc in _all_docs():
        for name in set(re.findall(r"([a-z][a-z-]+\.md)", doc.read_text())):
            if name == "SKILL.md":
                continue
            if not (REFS / name).exists():
                missing.append(f"{doc.name} -> {name}")
    assert not missing, missing


def test_every_reference_file_is_reachable_from_skill():
    text = SKILL.read_text()
    orphans = [p.name for p in REFS.glob("*.md") if p.name not in text]
    assert not orphans, f"SKILL.md never mentions: {orphans}"


def test_recipe_section_citations_resolve():
    recipes = (REFS / "craft-recipes.md").read_text() + (REFS / "craft-recipes-extras.md").read_text()
    have = set(re.findall(r"^## (\d+)\.", recipes, re.M))
    cited = set()
    for doc in _all_docs():
        cited |= set(re.findall(r"§\s?(\d+)", doc.read_text()))
    assert cited - have == set(), f"cited but missing: {sorted(cited - have, key=int)}"


def test_back_references_into_skill_resolve():
    have = set(re.findall(r"^## (\d+)\.", SKILL.read_text(), re.M))
    bad = []
    for doc in REFS.glob("*.md"):
        for n in re.findall(r"SKILL\.md section (\d+)", doc.read_text()):
            if n not in have:
                bad.append(f"{doc.name} -> section {n}")
    assert not bad, bad


def test_no_em_dashes_anywhere_in_the_skill():
    offenders = {d.name: d.read_text().count("—") for d in _all_docs()}
    assert not any(offenders.values()), offenders


def test_frontmatter_is_valid():
    head = SKILL.read_text().split("---")[1]
    assert re.search(r"^name: craft$", head, re.M)
    desc = re.search(r"^description: (.+)$", head, re.M).group(1)
    assert len(desc) < 600, "the description loads in every session; keep it short"
