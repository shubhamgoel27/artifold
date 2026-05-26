# Folio — OSS v0.1 plan

Brand: **Folio**. PyPI package: `ai-folio`. CLI command: `folio`.
Pattern: `pipx install ai-folio && folio init && folio` (scans + opens).

## Scope (v0.1, what shipped)
- [x] Renamed `report-organizer/` → `folio/`; brand strings updated
      everywhere ("Folio" wordmark, page title, theme key, SKIP_DIRS).
- [x] Package: `pyproject.toml` (hatchling), `console_script` →
      `folio = folio.cli:main`. Deps: platformdirs, playwright==1.51.0,
      watchdog. `pip install -e .` → 7 packages.
- [x] Split into modules: `scan.py`, `shoot.py`, `build.py`,
      `serve.py`, `cli.py`, `paths.py`, `config.py`, `template.html`
      (extracted from Python string).
- [x] CLI: `init`, `add`, `remove`, `roots`, `scan`, `serve`, `open`.
      Bare `folio` → serve + auto-open browser.
- [x] Config/cache via `platformdirs`:
      - config: `~/Library/Application Support/folio/config.json`
      - cache:  `~/Library/Caches/folio/` (index, data, thumbs, browsers)
- [x] Cross-platform: `webbrowser.open`, `Path` throughout, no bash left.
- [x] LICENSE (MIT), README rewrite (install / commands / config /
      keyboard / roadmap).
- [x] Features preserved: glass UI, theme toggle, ⌘K palette, preview
      pane, SSE auto-rescan, allowlist, variant collapsing.
- [x] OSS-generic: broader category keywords (Engineering/Health/Travel/
      Finance/Career/Education/Personal/Housing), extendable via config.
- [x] **Multi-root**: scan iterates across all configured roots.
- [x] **Security:** `/file` endpoint scope-checks against configured
      roots — `/etc/passwd` request returns 403.

## Out of scope for v0.1 (roadmap)
- AI essence summaries / semantic search
- Origin fingerprinting (Claude / v0 / Lovable detection)
- Re-prompt button
- React/Vue artifact rendering (needs build step)
- Windows testing

## Verification (all passed)
- `folio --version` → `folio 0.1.0`
- `folio init` + `folio add ~/work` → 15 projects, dashboard built into
  cache dir (16 minus coding-agents-workshop since allow_repos seeds
  empty by default — user can add it back via config)
- Dashboard renders cleanly with new "Folio" brand at hi-DPI
- `folio serve --port 8801`:
  - GET / → 200, GET /data.json → valid payload
  - GET /file?p=<under-root> → 200, /file?p=/etc/passwd → 403
  - touch watched .html → SSE `event: updated` delivered to client
