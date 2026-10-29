"""The file watcher must react to changes and ignore reads.

On Linux, watchdog's inotify backend reports every open and every
read-only close. A scan reads every page, so when the watcher treated
those as changes, each scan scheduled the next one: 123 scans and ~63,000
events in five minutes on an idle server. macOS never reports reads,
which is why it only showed up on Linux.
"""
import json
import sys
import threading
import time
from dataclasses import dataclass

import pytest

from artifold import config, serve


@dataclass
class Ev:
    """A watchdog event as the handler sees it, minus the version-specific
    class. The handler compares `event_type` strings, so this is enough."""
    event_type: str
    src_path: str
    dest_path: str = ""
    is_directory: bool = False


@pytest.fixture
def root(tmp_path, monkeypatch):
    root = tmp_path / "lib"
    (root / "proj").mkdir(parents=True)
    for f in ("proj/a.html", "proj/b.html", "top.html"):
        (root / f).write_text("<html><body>x</body></html>")
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"roots": [str(root)]}))
    monkeypatch.setattr(config, "CONFIG_FILE", cfg)
    return root.resolve()


@pytest.mark.parametrize("kind", ["opened", "closed_no_write"])
def test_reads_are_not_changes(root, kind):
    assert serve.library_change(Ev(kind, str(root / "proj" / "a.html"))) is None


@pytest.mark.parametrize("kind", ["created", "modified", "closed", "deleted"])
def test_writes_are_changes(root, kind):
    page = root / "proj" / "a.html"
    assert serve.library_change(Ev(kind, str(page))) == page


def test_atomic_save_counts_through_its_destination(root):
    page = root / "proj" / "a.html"
    ev = Ev("moved", str(page) + ".tmp", dest_path=str(page))
    assert serve.library_change(ev) == page


def test_moving_a_page_out_counts(root, tmp_path):
    page = root / "top.html"
    ev = Ev("moved", str(page), dest_path=str(tmp_path / "elsewhere.txt"))
    assert serve.library_change(ev) == page


def test_directory_events_are_ignored(root):
    assert serve.library_change(Ev("modified", str(root / "proj"), is_directory=True)) is None
    assert serve.library_change(Ev("created", str(root / "x.html"), is_directory=True)) is None


def test_non_library_paths_are_ignored(root):
    assert serve.library_change(Ev("modified", str(root / "proj" / "a.css"))) is None
    assert serve.library_change(Ev("modified", str(root / "node_modules" / "x.html"))) is None


def test_the_strings_match_watchdog():
    """The filter compares strings; pin them to the installed watchdog so a
    rename there fails here instead of silently bringing the loop back."""
    events = pytest.importorskip("watchdog.events")
    assert events.FileOpenedEvent.event_type == "opened"
    closed_no_write = getattr(events, "FileClosedNoWriteEvent", None)   # watchdog >= 5
    if closed_no_write is not None:
        assert closed_no_write.event_type == "closed_no_write"
    assert set(serve.READ_ONLY_EVENTS) == {"opened", "closed_no_write"}


@pytest.mark.skipif(not sys.platform.startswith("linux"),
                    reason="only inotify reports reads")
def test_reading_the_library_schedules_no_scan(root, monkeypatch):
    """The real watcher on a real inotify backend: read every page the way a
    scan does, and nothing may be scheduled. Then one write, one scan."""
    pytest.importorskip("watchdog")
    scans, reads = [], []
    lock = threading.Lock()
    monkeypatch.setattr(serve, "DEBOUNCE", 0.2)
    monkeypatch.setattr(serve, "_run_scan", lambda reason: scans.append(reason))
    real = serve.library_change

    def spy(ev):                     # proves the reads really reached us
        if ev.event_type in serve.READ_ONLY_EVENTS:
            with lock:
                reads.append(ev.event_type)
        return real(ev)
    monkeypatch.setattr(serve, "library_change", spy)

    obs = serve._start_watcher()
    assert obs is not None
    try:
        time.sleep(0.3)              # let inotify settle
        for _ in range(3):
            for f in root.rglob("*.html"):
                f.read_text(encoding="utf-8", errors="ignore")
        time.sleep(3 * serve.DEBOUNCE + 0.3)
        assert reads, "inotify sent no read events; the test proves nothing"
        assert scans == []

        (root / "proj" / "a.html").write_text("<html><body>edited</body></html>")
        time.sleep(3 * serve.DEBOUNCE + 0.3)
        assert scans == ["auto"]
    finally:
        obs.stop()
        obs.join(timeout=2)
