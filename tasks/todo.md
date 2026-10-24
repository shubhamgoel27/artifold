# Report Organizer — Plan

A static, self-contained dashboard for the ~369 HTML reports under `~/work`.
Refresh = run one script. Cards show screenshot thumbnails.

## Architecture
- `organize.py` — single entrypoint, 3 phases:
  1. **scan** — walk `~/work`, find `*.html` (skip node_modules/.git/dist/the organizer itself).
     Group by directory into "projects". Top-level loose `.html` = their own project.
     Extract: `<title>`, first heading, first paragraph snippet, mtime, size.
     Pick a **primary** file per project (index.html > shortest name > newest); rest = variants.
     Auto-categorize by keyword heuristics on path+title.
  2. **shoot** — Playwright (chromium) screenshots each primary report → `thumbs/<hash>.jpg`.
     Incremental: `manifest.json` keyed on (path, mtime, size); only re-shoot changed.
     Async with a small concurrency semaphore.
  3. **build** — emit self-contained `index.html` with embedded JSON, client-side
     search (full-text over title+heading+snippet), category filter chips,
     sort (default: most recently generated), thumbnails as relative files.
- `refresh.sh` — `uv run` wrapper so a single command rebuilds everything.

## Decisions locked
- Static + refresh script (no server). Screenshot thumbnails (Playwright).
- Group by project; collapse index/print/v1 variants behind a primary card.
- Default sort = file mtime (recency). Full-text search.

## Todo
- [x] scaffold project
- [x] organize.py: scan phase
- [x] organize.py: shoot phase (incremental cache)
- [x] organize.py: build phase (index.html template)
- [x] refresh.sh + README
- [x] first full run, verify thumbnails + search work

## Review
- Built in `~/work/report-organizer/`. `./refresh.sh` is the one command.
- Scan found 166 raw html files; nested-`.git` filter (skip cloned repos like
  pandas/iina/wandb-mlops/ml-intern) reduced to **12 real report projects, 30 files**.
- Playwright chromium installed to local `.pw-browsers/`; 12 thumbnails shot
  (50–139KB each, verified non-blank). Incremental cache via `manifest.json`
  + mtime/size hash — re-runs only re-shoot changed reports.
- index.html: full-text search, category chips, recency sort, variant links.
  Self-contained, opens with no server.
- Known tradeoff: nested-.git skip also drops coding-agents-workshop slides.
  Tunable via SKIP_DIRS / the `.git` check in organize.py if wanted back.

## Follow-up: rescan button + allowlist
- [x] `.git` skip → allowlist via auto-created `config.json`
      (`allow_repos`, seeded with coding-agents-workshop). Now 13 projects.
- [x] `serve.py` (zero-dep stdlib) + `serve.sh` — serves dashboard, POST
      /rescan re-runs organize.py. Tested: index/thumb 200, rescan ok:true.
- [x] index.html: `↻ Rescan` button. file:// → copy-command toast;
      served → live rescan + reload. Graceful fallback on fetch fail.

## Follow-up: 2026 visual redesign
- [x] Animated aurora backdrop (3 drifting blurred orbs, blend-screen).
- [x] Glassmorphism: blurred translucent surfaces, hairline borders,
      sticky frosted top bar, soft depth shadows.
- [x] Per-category color system (8 hues) → chip dots/active fill, card
      badge dots, gradient hover border + glow + title.
- [x] Card polish: 20px radius, img zoom on hover, scrim, lift,
      staggered fade-up entrance. Gradient wordmark + glow dot.
- [x] Pure CSS, no CDNs/fonts (offline-safe). prefers-reduced-motion
      respected. Verified hi-DPI incl. hover state. JS logic untouched.

## Follow-up: theme toggle + scan correctness
- [x] Dark/light theme button. Themed via CSS var sets on
      `:root[data-theme]`; persists in localStorage; honors
      prefers-color-scheme; no-flash init script in <head>. Both verified.
- [x] Distinct reports in a folder now each get a card (health-plan,
      socal-trip, strength-training, eb1 → 2 cards). Only true export
      variants (print/v1/one-page/…) collapse, via VARIANT_RE.
- [x] Excluded server templates ({% %} block tags), `templates/` etc.
      dirs, and html buried >3 levels deep — kills the annu_backup
      grad-archive + the bogus "baselines" Django index.
- [x] Caught + fixed regex false-positive: `}}` matched legit CSS/JS
      and wrongly dropped a real eb1 report. Now {%-only. 16 proj/18 files.

## Follow-up: --no-shoot thumbnail footgun
- [x] Extracted `resolve_cached_thumbs()` — points projects at cached
      thumbs by mtime/size key. Used by both shoot() (DRY) and the
      --no-shoot path. `--no-shoot` now reuses 16/16 cached thumbs
      instead of nulling all previews. Reports kept count.

## Tier 1: UX core
- [x] **Preview pane** — slide-in right panel + scrim. Plain card click
      opens; modifier-clicks honor new-tab. Header has title/dir/cat +
      open-in-new-tab + close. Body scroll locks. Esc closes.
- [x] **⌘K palette** — fuzzy scoring over name+dir+category. ↑↓ nav,
      ↵ → preview, ⇧↵ → new tab, esc closes. `/` focuses search.
      Headless-tested: "strn" → Strength Training Tracker top hit.
- [x] **Auto-rescan** — serve.py runs a watchdog observer on the root,
      ignores its own outputs + known noise dirs, debounces 2s, broadcasts
      over SSE. Dashboard hot-swaps data.json + flashes "Library updated".
      Tested end-to-end: touch → rescan ok in 10s → SSE `event: updated`.
- [x] Fixed playwright version-drift footgun. Pinned to `==1.51.0`,
      install call made idempotent (no dir-check). Caught after uv
      silently resolved newer playwright that wanted a chromium build
      our cache didn't have.

## v0.15: traction pass (2026-10-22)
- [x] 2. Rerun the gallery with today's craft (Opus 5.5): same 11 prompts,
      plain side via `claude -p --disable-slash-commands`, craft side via
      `/craft`. Re-shoot thumbs, rebuild the 3 composites with a script so
      it is repeatable, update docs/index.html. README stops saying
      "an earlier version".
- [x] 3. Claude Code plugin: manifest + marketplace in the repo so
      `/plugin` installs craft with no Python. README install updated.
- [x] 5. Share credit footer: shared copy (never the local file) gets a
      small "Made with craft" / "Shared with Artifold" link. Setting
      `share_credit` (on by default), tests.
- [x] 1. Fresh dashboard screenshots + demo GIF from a demo library built
      from gallery pages (isolated HOME, so no private pages), after 2.

### Review
- Gallery: Opus 5.5 without a skill designs much better than 4.7 did, so
  the gap narrowed. craft wins clearly on 5 of 11; the rest are close.
  Clear wins lead the grid; the README opening no longer claims plain
  Claude makes purple gradients.
- Two craft pages leaked the user's name and employers through the
  library. Rerun against an empty, isolated library; whole-word scan of
  all 22 pages is clean.
- Old README screenshots showed the old name (Folio) and private pages.
  Replaced from a throwaway library.

## v0.16: hide (2026-10-24)
Hide a page from the dashboard without touching the file.
- [x] Store: `hidden` flag on the provenance entry of every file in the
      project (survives renames, since the hash is the key, and in-place
      edits through carry_forward; a new -v2 stays hidden because the
      older versions are). Folders: `hidden_dirs` in config, so new
      files in a hidden folder stay hidden.
- [x] Scan: each project gets `hidden: "self" | "folder"` (absent when
      visible), plus `hidden_dir`.
- [x] Server: POST /hide {paths | dir, hidden}. Paths outside a root
      are refused, like /trash.
- [x] Dashboard: hidden pages leave the grid, counts and ⌘K. A "Hidden"
      view in the sidebar (shown only when there are some) lists them.
      Hide/unhide button on the card and in the detail header. The toast
      offers Undo and "Hide folder".
- [x] CLI: `artifold hide <file|dir>`, `artifold unhide <file|dir>`,
      `artifold hidden`. `search` skips hidden unless `--all`.
- [x] Tests, CHANGELOG, README, version 0.16.0, release.

### Review
- Browser run on a throwaway library: hide from a card, Undo, "Hide all
  of <folder>", Hidden view, unhide from the detail header and from a
  folder-hidden card, state kept across a reload. No console errors;
  files untouched.
- CLI run with and without a live server: `serve` now writes its port to
  the cache dir, so `artifold hide` asks only its own library's server
  to rescan, and rebuilds data.json itself when none runs.
- Byte-identical copies share a provenance entry, so they hide together.
  Kept: it is how tags and shares already treat duplicates.
