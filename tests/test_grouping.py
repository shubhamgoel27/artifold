"""Tests for scan grouping: date-prefixed slugs, top-level version collapse."""
import time

from artifold import scan


def test_strip_date():
    assert scan._strip_date("2026-06-09-dsa-concept-bible") == \
        ("2026-06-09", "dsa-concept-bible")
    assert scan._strip_date("report-v2") == ("", "report-v2")
    # a bare date stem keeps its name rather than becoming empty
    assert scan._strip_date("2026-06-09") == ("", "2026-06-09")


def test_classify_strips_date_before_versioning():
    assert scan._classify("2026-06-09-dsa-concept-bible") == \
        ("main", "dsa-concept-bible", 1)
    assert scan._classify("2026-06-10-dsa-concept-bible") == \
        ("main", "dsa-concept-bible", 1)
    assert scan._classify("curbcheck-report-v2") == \
        ("version", "curbcheck-report", 2)
    assert scan._classify("2026-06-12-report-v3") == \
        ("version", "report", 3)
    assert scan._classify("2026-06-12-foo-print") == ("variant", "foo-print", 1)


def _write(p, title):
    p.write_text(f"<html><head><title>{title}</title></head>"
                 f"<body><h1>{title}</h1></body></html>")


def test_top_level_date_iterations_group_as_versions(tmp_path):
    """Two dated inbox files with the same slug = one project, two versions."""
    _write(tmp_path / "2026-06-09-dsa-concept-bible.html", "DSA Bible")
    time.sleep(0.02)
    _write(tmp_path / "2026-06-10-dsa-concept-bible.html", "DSA Bible v2")
    _write(tmp_path / "2026-06-14-cross-entropy.html", "Cross Entropy")

    projects = scan._scan_root(tmp_path, {"allow_repos": [], "max_depth": 3},
                               {}, {})
    assert len(projects) == 2
    bible = next(p for p in projects if "bible" in p["id"])
    assert bible["version_count"] == 2
    # newest file wins primary, and versions are renumbered chronologically
    assert bible["primary"]["rel"] == "2026-06-10-dsa-concept-bible.html"
    assert bible["current_version"] == 2
    assert [v["version"] for v in bible["versions"]] == [2, 1]


def test_top_level_v2_suffix_groups(tmp_path):
    _write(tmp_path / "curbcheck-report.html", "Curbcheck")
    _write(tmp_path / "curbcheck-report-v2.html", "Curbcheck v2")

    projects = scan._scan_root(tmp_path, {"allow_repos": [], "max_depth": 3},
                               {}, {})
    assert len(projects) == 1
    assert projects[0]["version_count"] == 2
    assert projects[0]["primary"]["rel"] == "curbcheck-report-v2.html"


def test_distinct_top_level_files_stay_separate(tmp_path):
    _write(tmp_path / "2026-06-07-scalp-routine-card.html", "Scalp")
    _write(tmp_path / "2026-06-07-netflix-explainer.html", "Netflix")

    projects = scan._scan_root(tmp_path, {"allow_repos": [], "max_depth": 3},
                               {}, {})
    assert len(projects) == 2
    assert all(p["version_count"] == 1 for p in projects)
