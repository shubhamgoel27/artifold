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
import hashlib
import json
import mimetypes
import queue
import re
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

# Safe asset types — served alongside an HTML artifact via /asset/<token>/<rel>.
# Anything not in this set 404s, so secrets like .env / .key / .pem / .py can
# never leak even from a configured root.
ALLOWED_ASSET_EXTS = {
    # Markup / data
    ".html", ".htm", ".xml", ".json", ".txt", ".md", ".csv", ".tsv",
    # Styles / scripts
    ".css", ".js", ".mjs", ".map",
    # Images / vectors
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".bmp",
    # Fonts
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # Media (occasional)
    ".mp4", ".webm", ".ogg", ".mp3", ".wav",
}

_subscribers: set[queue.Queue] = set()
_sub_lock = threading.Lock()
_rescan_lock = threading.Lock()
# When an event arrives while a scan is already in-flight, instead of
# dropping it we set this flag. The in-flight scan checks it on completion
# and fires one follow-up — so changes made during long scans aren't lost.
_rescan_pending = False
_rescan_pending_lock = threading.Lock()

# Map of short hash → resolved Path of the artifact's containing dir.
# Populated lazily when /file?p=<html> is served. Persists for the server's
# lifetime; cleared on restart (which is fine — dashboard requests will
# re-populate by re-loading the iframe).
_dir_tokens: dict[str, Path] = {}
_dir_tokens_lock = threading.Lock()


def _broadcast(event: str, data: str = "ok") -> None:
    with _sub_lock:
        for q in list(_subscribers):
            try:
                q.put_nowait((event, data))
            except Exception:
                pass


def _run_scan(reason: str) -> bool:
    """Synchronous scan → shoot → build, one at a time. Returns success.

    Concurrency: when called during another scan, sets a 'pending' flag
    instead of dropping the request. The active scan checks the flag on
    completion and spawns a follow-up, so events that arrived during the
    scan window are never lost.
    """
    global _rescan_pending
    if not _rescan_lock.acquire(blocking=False):
        with _rescan_pending_lock:
            _rescan_pending = True
        print(f"  (scan in progress; queued follow-up for [{reason}])")
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
        # If anything was queued while we held the lock, fire one follow-up.
        # Doing this in a daemon thread keeps _run_scan synchronous for callers.
        with _rescan_pending_lock:
            should_followup = _rescan_pending
            _rescan_pending = False
        if should_followup:
            threading.Thread(target=_run_scan, args=("queued-follow-up",),
                             daemon=True).start()


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


def _token_for_dir(d: Path) -> str:
    """Register `d` and return a stable 12-char hash used in /asset/<token>/…
    URLs. Same dir → same token across calls."""
    d = d.resolve()
    tok = hashlib.sha1(str(d).encode("utf-8")).hexdigest()[:12]
    with _dir_tokens_lock:
        _dir_tokens[tok] = d
    return tok


_HEAD_OPEN_RE     = re.compile(rb"<head\b[^>]*>", re.I)
_HTML_OPEN_RE     = re.compile(rb"<html\b[^>]*>", re.I)
_BASE_EXISTS_RE   = re.compile(rb"<base\b[^>]*>", re.I)
# Tolerate utf-8 BOM and leading whitespace before <!doctype>
_DOCTYPE_RE       = re.compile(rb"<!doctype[^>]*>", re.I)


def _inject_base_href(html_bytes: bytes, base_url: str) -> bytes:
    """Inject `<base href="<base_url>">` into <head> if not already present.
    Fails open: if the HTML has no recognisable structure, return unchanged."""
    if _BASE_EXISTS_RE.search(html_bytes[:8192]):
        return html_bytes  # respect existing base
    tag = f'<base href="{base_url}">'.encode("utf-8")
    m = _HEAD_OPEN_RE.search(html_bytes)
    if m:
        idx = m.end()
        return html_bytes[:idx] + tag + html_bytes[idx:]
    # No <head> — try inserting after <html> opening
    m = _HTML_OPEN_RE.search(html_bytes)
    if m:
        idx = m.end()
        return html_bytes[:idx] + b"<head>" + tag + b"</head>" + html_bytes[idx:]
    # No <html> — try inserting after <!doctype> or at very top
    m = _DOCTYPE_RE.search(html_bytes)
    if m:
        idx = m.end()
        return html_bytes[:idx] + b"\n<head>" + tag + b"</head>" + html_bytes[idx:]
    return tag + html_bytes  # last resort — still valid HTML, browser will tolerate


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
        if path == "/export-pdf":
            return self._handle_export_pdf()
        if path == "/trash":
            return self._handle_trash()
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
            return self._json({"ok": False, "error": "import failed - see terminal"}, 500)
        threading.Thread(target=_run_scan, args=("import-followup",), daemon=True).start()
        return self._json({"ok": True, "path": str(out)})

    def _handle_trash(self):
        from . import trash as trash_mod
        body = self._read_json()
        p = body.get("path")
        if not p:
            return self._json({"ok": False, "error": "path required"}, 400)
        target = Path(p)
        if not _allowed_path(target):
            return self._json({"ok": False, "error": "path not under any configured root"}, 403)
        ok, msg = trash_mod.trash_file(target)
        if not ok:
            return self._json({"ok": False, "error": msg}, 500)
        # Watchdog will catch the deletion and trigger a debounced rescan,
        # but that's a 2s wait. Fire one immediately so the UI updates fast.
        threading.Thread(target=_run_scan, args=("trash-followup",), daemon=True).start()
        return self._json({"ok": True, "trashed": msg})

    def _handle_export_pdf(self):
        from . import pdf as pdf_mod
        body = self._read_json()
        p = body.get("path")
        if not p:
            return self._json({"ok": False, "error": "path required"}, 400)
        target = Path(p)
        if not _allowed_path(target):
            return self._json({"ok": False, "error": "path not under any configured root"}, 403)
        try:
            opts = {
                "format": body.get("format") or "A4",
                "landscape": bool(body.get("landscape")),
                "print_backgrounds": body.get("print_backgrounds", True),
                "margin": body.get("margin") or "12mm",
            }
            out = pdf_mod.export_pdf(target, **opts)
        except ValueError as e:
            return self._json({"ok": False, "error": str(e)}, 400)
        except Exception as e:
            return self._json({"ok": False, "error": f"export failed: {e}"}, 500)
        # Re-scan in the background so provenance update lands in the UI
        threading.Thread(target=_run_scan, args=("export-followup",), daemon=True).start()
        return self._json({"ok": True, "path": str(out), "size": out.stat().st_size})

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
            # For HTML artifacts, register the containing dir and inject
            # `<base href="/asset/<token>/">` so relative sibling refs
            # (./styles.css, ./app.js, ./img/foo.png) resolve via /asset/.
            if (mime or "").startswith("text/html"):
                tok = _token_for_dir(target.parent)
                data = _inject_base_href(data, f"/asset/{tok}/")
                mime = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # /asset/<token>/<rel> — siblings of an HTML artifact under a dir
        # previously registered by /file. The token scheme means the URL
        # alone doesn't reveal the actual server-side path; we still
        # double-check the resolved path against configured roots.
        if path.path.startswith("/asset/"):
            return self._handle_asset(path)

        # /open?p=…   open a file with the system default app (macOS: `open`)
        # /reveal?p=… reveal a file in Finder (macOS: `open -R`)
        # Both refuse paths outside any configured root.
        if path.path in ("/open", "/reveal"):
            return self._handle_system_action(path)

        # /designs/<sha>?format=css|skeleton|template
        if path.path.startswith("/designs/"):
            return self._handle_designs(path)

        # bare "/" → index.html in cache dir
        if path.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def _handle_asset(self, path):
        """Serve a sibling asset for an HTML artifact.

        URL shape:  /asset/<12-hex-token>/<relative/path/to/file.ext>
        Rules:
          - <token> must be in `_dir_tokens` (registered by /file?p=…)
          - <relative> must not escape the registered dir (no `..`)
          - resolved path must still be under a configured root
          - extension must be in ALLOWED_ASSET_EXTS
        """
        # Strip prefix, split off token
        rest = path.path[len("/asset/"):]
        if "/" not in rest:
            return self.send_error(404)
        token, _, rel = rest.partition("/")
        if not re.fullmatch(r"[0-9a-f]{12}", token):
            return self.send_error(400, "bad token")
        with _dir_tokens_lock:
            base = _dir_tokens.get(token)
        if not base:
            # Token expired (server restarted) — tell the browser
            return self.send_error(404, "asset token unknown - reload the page")
        # urldecode the relative path; reject anything trying to escape
        rel = urllib.parse.unquote(rel)
        if not rel or rel.startswith("/"):
            return self.send_error(400, "bad relative path")
        # Resolve and validate containment
        try:
            target = (base / rel).resolve(strict=True)
            target.relative_to(base)
        except (ValueError, OSError):
            return self.send_error(404)
        if not target.is_file():
            return self.send_error(404)
        if target.suffix.lower() not in ALLOWED_ASSET_EXTS:
            return self.send_error(404, "asset type not allowed")
        if not _allowed_path(target):
            return self.send_error(403, "asset outside configured roots")
        mime, _ = mimetypes.guess_type(str(target))
        try:
            data = target.read_bytes()
        except Exception:
            return self.send_error(500)
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        # Long cache for assets — they're content-addressed by token (which
        # changes when the source dir path changes)
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(data)

    def _handle_system_action(self, path):
        """Open or reveal a local file. Used by the dashboard's PDF-exported
        toast: 'Open' (opens in default PDF viewer) / 'Reveal in Finder'.
        Only files under a configured root are honoured (no arbitrary disk)."""
        import subprocess
        import platform
        qs = urllib.parse.parse_qs(path.query)
        p = (qs.get("p") or [""])[0]
        if not p:
            return self.send_error(400)
        target = Path(p)
        # PDFs live next to source HTML inside roots, OR in ~/Downloads.
        # Allow both: root-relative OR ~/Downloads/ files we wrote ourselves.
        downloads = (Path.home() / "Downloads").resolve()
        try:
            target_r = target.resolve(strict=True)
        except OSError:
            return self.send_error(404)
        under_downloads = False
        try:
            target_r.relative_to(downloads)
            under_downloads = True
        except ValueError:
            pass
        if not (under_downloads or _allowed_path(target)):
            return self.send_error(403)
        sys_name = platform.system().lower()
        try:
            if sys_name == "darwin":
                args = (["open", "-R", str(target_r)] if path.path == "/reveal"
                        else ["open", str(target_r)])
            elif sys_name == "linux":
                args = ["xdg-open", str(target_r.parent if path.path == "/reveal" else target_r)]
            elif sys_name == "windows":
                if path.path == "/reveal":
                    args = ["explorer", "/select,", str(target_r)]
                else:
                    args = ["explorer", str(target_r)]
            else:
                return self.send_error(501, "unsupported platform")
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            return self.send_error(500, f"open failed: {e}")
        return self._json({"ok": True})

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


# Use scan.py's SKIP_DIRS as the single source of truth so the watcher and
# the scanner agree about what to ignore. Previously these drifted: the
# watcher was firing scans for changes inside `artifold/` itself (in
# SKIP_DIRS) and the scanner then ignored them — wasting a ~9.5s scan per
# event and blocking real changes via the in-flight lock.
from .scan import SKIP_DIRS as _SKIP_DIRS


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
            # For atomic-write rename patterns (editor saves as foo.html.tmp
            # then `mv foo.html.tmp foo.html`), the move event's src_path is
            # the .tmp file which would be filtered out. Check dest_path too.
            paths = [getattr(ev, "src_path", "")]
            dest = getattr(ev, "dest_path", "")  # only set on FileMovedEvent
            if dest:
                paths.append(dest)
            for sp in paths:
                if not sp:
                    continue
                p = Path(sp)
                if not p.name.lower().endswith(".html"):
                    continue
                try:
                    if CACHE_DIR in p.parents:
                        continue
                except Exception:
                    pass
                if any(part in _SKIP_DIRS for part in p.parts):
                    continue
                # Survived all filters — schedule a debounced scan and log it
                # so the operator can see the watcher is alive and working.
                try:
                    rel = p.relative_to(Path.home())
                    label = f"~/{rel}"
                except ValueError:
                    label = str(p)
                kind = type(ev).__name__.replace("File", "").replace("Event", "").lower()
                print(f"  • watch: {kind} {label}  (scan in {DEBOUNCE:.0f}s)")
                schedule()
                return  # one schedule per event is enough

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
