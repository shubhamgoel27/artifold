"""HTTP server for the dashboard.

- Serves index.html / data.json / thumbs/ from the cache dir.
- GET /file?p=<absolute_path> serves any report under a configured root
  (path scoped to roots, so this can't read arbitrary disk).
- POST /rescan re-runs the scan and broadcasts.
- GET /events is a Server-Sent Events stream — client hot-swaps data.json.
- watchdog auto-rescans on *.html changes under any root (debounced).
"""
from __future__ import annotations

import asyncio
import json
import mimetypes
import queue
import sys
import threading
import time
import urllib.parse
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import config
from .paths import CACHE_DIR, DATA

DEBOUNCE = 2.0

_subscribers: set[queue.Queue] = set()
_sub_lock = threading.Lock()
_rescan_lock = threading.Lock()


def _broadcast(event: str, data: str = "ok") -> None:
    with _sub_lock:
        for q in list(_subscribers):
            try:
                q.put_nowait((event, data))
            except Exception:
                pass


def _run_scan(reason: str) -> bool:
    """Synchronous scan → shoot → build, one at a time. Returns success."""
    if not _rescan_lock.acquire(blocking=False):
        print(f"  (scan already running; skipping {reason})")
        return False
    try:
        from . import scan as scan_mod, shoot as shoot_mod, build as build_mod
        print(f"→ scan [{reason}]…")
        t0 = time.time()
        try:
            projects = scan_mod.scan_all()
            asyncio.run(shoot_mod.shoot(projects))
            build_mod.build(projects, [str(r) for r in config.roots()])
        except Exception as e:
            print(f"  scan FAILED: {e}")
            return False
        print(f"  scan ok in {time.time()-t0:.1f}s")
        _broadcast("updated", reason)
        return True
    finally:
        _rescan_lock.release()


def _allowed_path(p: Path) -> bool:
    """True if p is inside any configured root (after resolving symlinks)."""
    try:
        p = p.resolve(strict=True)
    except Exception:
        return False
    for r in config.roots():
        try:
            p.relative_to(r.resolve())
            return True
        except ValueError:
            continue
    return False


class Handler(SimpleHTTPRequestHandler):

    def do_POST(self):
        path = self.path.rstrip("/")
        if path == "/rescan":
            ok = _run_scan("manual")
            return self._json({"ok": ok}, status=200 if ok else 500)
        if path == "/share":
            return self._handle_share()
        if path == "/import":
            return self._handle_import()
        self.send_error(404)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n: return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def _json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_share(self):
        from . import share as share_mod
        body = self._read_json()
        p = body.get("path")
        if not p:
            return self._json({"ok": False, "error": "path required"}, 400)
        target = Path(p)
        if not _allowed_path(target):
            return self._json({"ok": False, "error": "path not under any configured root"}, 403)
        url = share_mod.share_via_gh(target, no_clipboard=True)
        if not url:
            return self._json({"ok": False, "error": "share failed — check terminal for details"}, 500)
        # Quick re-scan so the dashboard's data reflects the new share record.
        threading.Thread(target=_run_scan, args=("share-followup",), daemon=True).start()
        return self._json({"ok": True, "url": url})

    def _handle_import(self):
        from . import importer
        body = self._read_json()
        url = (body.get("url") or "").strip()
        if not url:
            return self._json({"ok": False, "error": "url required"}, 400)
        out = importer.import_url(url)
        if not out:
            return self._json({"ok": False, "error": "import failed — see terminal"}, 500)
        threading.Thread(target=_run_scan, args=("import-followup",), daemon=True).start()
        return self._json({"ok": True, "path": str(out)})

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path)

        if path.path.rstrip("/") == "/events":
            self._stream_events(); return

        if path.path == "/file":
            qs = urllib.parse.parse_qs(path.query)
            p = (qs.get("p") or [""])[0]
            if not p:
                self.send_error(400); return
            target = Path(p)
            if not _allowed_path(target):
                self.send_error(403, "path not under any configured root"); return
            mime, _ = mimetypes.guess_type(str(target))
            try:
                data = target.read_bytes()
            except Exception:
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # /designs/<sha>?format=css|skeleton|template
        if path.path.startswith("/designs/"):
            return self._handle_designs(path)

        # bare "/" → index.html in cache dir
        if path.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def _handle_designs(self, path):
        from . import design as design_mod, provenance
        import urllib.parse as up
        sha_prefix = path.path[len("/designs/"):].strip("/")
        if not sha_prefix or not sha_prefix.isalnum():
            return self.send_error(400)
        # Find a project with that SHA1 prefix in current data
        try:
            d = json.loads(DATA.read_text())
        except Exception:
            return self.send_error(503, "no scan data yet")
        target = None
        for proj in d.get("projects") or []:
            for v in (proj.get("versions") or [proj.get("primary")]):
                if (v or {}).get("sha1", "").startswith(sha_prefix):
                    target = v.get("path"); break
            if target: break
        if not target:
            return self.send_error(404)
        if not _allowed_path(Path(target)):
            return self.send_error(403)
        html = Path(target).read_text(encoding="utf-8", errors="ignore")
        qs = up.parse_qs(path.query)
        fmt = (qs.get("format") or ["template"])[0]
        if fmt == "css":
            out = "\n\n".join(s.strip() for s in design_mod.STYLE_RE.findall(html))
        elif fmt == "skeleton":
            out = design_mod.as_template(html, include_css=False, include_skeleton=True)
        else:
            out = design_mod.as_template(html)
        body = out.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _stream_events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q: queue.Queue = queue.Queue()
        with _sub_lock:
            _subscribers.add(q)
        try:
            self.wfile.write(b": connected\n\n"); self.wfile.flush()
            while True:
                try:
                    ev, data = q.get(timeout=20)
                    self.wfile.write(f"event: {ev}\ndata: {data}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n"); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _sub_lock:
                _subscribers.discard(q)

    def log_message(self, *_a):
        pass


IGNORE_NAMES = {"node_modules", ".git", ".next", "dist", "build", "__pycache__",
                ".venv", "venv", "out", "coverage", ".cache",
                "templates", "site-packages", ".tox", "migrations", "vendor"}


def _start_watcher():
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("  ! watchdog not installed — auto-rescan disabled.\n"
              "    pip install watchdog")
        return None

    roots = config.roots()
    if not roots:
        print("  ! no roots configured — auto-rescan disabled "
              "(run `artifold add <dir>`).")
        return None

    pending = {"t": None}

    def schedule():
        if pending["t"]:
            pending["t"].cancel()
        pending["t"] = threading.Timer(DEBOUNCE, lambda: _run_scan("auto"))
        pending["t"].daemon = True
        pending["t"].start()

    class H(FileSystemEventHandler):
        def on_any_event(self, ev):
            if ev.is_directory:
                return
            p = Path(getattr(ev, "src_path", ""))
            if not p.name.endswith(".html"):
                return
            try:
                if CACHE_DIR in p.parents:
                    return
            except Exception:
                pass
            if any(part in IGNORE_NAMES for part in p.parts):
                return
            schedule()

    obs = Observer()
    for r in roots:
        if r.is_dir():
            obs.schedule(H(), str(r), recursive=True)
            print(f"  watching {r} for *.html changes (debounce {DEBOUNCE}s)")
    obs.daemon = True
    obs.start()
    return obs


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that silences benign client-disconnect tracebacks.

    Browsers routinely open TCP connections they don't end up sending requests
    on (keep-alive, pre-connect, EventSource reconnects, devtools prefetch).
    The stdlib server prints a full traceback for each one. Silence those
    while still surfacing real errors.
    """
    _benign = (ConnectionResetError, BrokenPipeError, ConnectionAbortedError,
               TimeoutError)

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, self._benign):
            return                              # client dropped; nothing to do
        super().handle_error(request, client_address)


def serve(port: int = 8787, open_browser: bool = True) -> None:
    if not DATA.exists():
        print("  no dashboard yet — running an initial scan…")
        _run_scan("initial")

    obs = _start_watcher()
    httpd = QuietThreadingHTTPServer(("127.0.0.1", port),
                                     partial(Handler, directory=str(CACHE_DIR)))
    url = f"http://127.0.0.1:{port}/"
    print(f"\nArtifold live at {url}\n"
          f"(Ctrl+C to stop · ⌘K palette · auto-rescans on changes)\n")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        if obs:
            obs.stop(); obs.join(timeout=2)
