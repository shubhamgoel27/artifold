# Changelog

## 0.10.0

Artifold is now the library for whatever design skill you use, not the app
that goes with `/craft`.

This came out of reading the competition properly. The design-skill
category is crowded — taste-skill has 83.3k stars, Hallmark 27.7k,
huashu-design 23.8k — and nothing at all indexes a local corpus of
AI-generated HTML. More useful still: of those three, only Hallmark
records anything between runs, and its log is per-repository. Remembering
what you already made, across projects, is the thing none of them do.

### A metadata convention anybody can emit

[`docs/ARTIFACT-METADATA.md`](docs/ARTIFACT-METADATA.md) documents the
`artifold:*` meta tags as a plain convention for design-skill authors. Four
lines of `<head>` and a generated page can say what it is for. No
dependency on Artifold to write them or to read them.

New `artifold:generator` tag names the skill that built a page, separate
from `tool`, which names the model vendor. `/craft` now emits it.

### Adapters for skills that stamp their own format

`artifold/adapters.py` reads other tools' markers. Hallmark ships first: its
CSS stamp gives layout, theme, tone and hue, and `.hallmark/log.json` gives
the brief, which lands as `intent`. Foreign vocabulary maps onto Artifold's
fields — a macrostructure is not exactly a layout archetype, so the raw
values are kept under `generator_native` rather than thrown away.

Adapters rank below native tags: a skill that states its intent always
beats one inferred from a stamp. They fail soft by design, because these
are other people's formats and they move — an unparseable stamp yields no
metadata, never an error.

### `artifold skills`

Shows which design skills you have installed and, honestly, how much
Artifold recovers from each: `native` (everything), `adapter` (layout,
theme, brief) or `fingerprint` (palette, fonts, tokens, skeleton, search).
That last tier needs no cooperation and is most of the product.

### Also

- README reframed: `/craft` is the bundled reference implementation, not
  the point. Hallmark and taste-skill are linked as real alternatives.

## 0.9.0

A second audit of a real library, five weeks and 43 artifacts after the
first. At 133 projects the questions change: not "where is it" but "which
of these do I actually use".

### Your edit history was recorded, hidden, and expiring

Artifold has always carried provenance across an in-place edit. It never
showed the result. A real library held 128 of these superseded entries —
16 artifacts with revisions, the longest chains 28 and 17 deep — while the
version dropdown, which reads `-v2` filenames, matched 2 of 133 projects.

Worse, the history was on a timer. A superseded entry's content hash is
gone from disk by definition, so the orphan rule stamped every one of them
for deletion 30 days out. All 128 were counting down.

- `gc` now exempts revisions reachable from a live artifact, and clears the
  stamp from ones already marked.
- `carry_forward` stamps `revised_at` and `superseded_at`, so the chain has
  time in it. `added_at` stays put: a revision is not a new artifact.
- Cards show a revision badge; the detail pane lists the history.

Revisions cannot be diffed — the store keeps hashes, not content — and the
pane says so instead of offering a button that cannot work. Chains recorded
before this release have no times, so that case shows the count alone.

### Artifold now knows what you use, not just what you made

Creation time cannot answer "what do I keep coming back to", and after a
hundred artifacts that is the question.

- Opening an artifact is counted, via `/open` and a `POST /opened` beacon
  for new-tab opens. Previewing a card is not an open, and revealing in
  Finder is not a read.
- New "Most used" sort, ranking opens 3× revisions. Opens start at zero
  everywhere, so revisions carry the sort until real data accrues.
- Requires `artifold serve`; a `file://` dashboard has no server to tell.

### Cache and clutter

- **Thumbnails are garbage-collected** on a full scan. The cache key is
  sha1(path+mtime+size), so every edit stranded the previous image and
  nothing ever cleaned up: 513 files, 380 of them orphans, 32.4 MB of 44 MB.
  A real library drops to 133 files and 12 MB. Stale manifest rows go too.
- **The parsed provenance store is memoized.** One scan called `_load_raw`
  670 times, re-reading 546 KB each time. Scans run in ~2.3 s where they
  took ~3.2 s, despite doing more work.
- **The tool filter and the per-card tool label hide** unless the library
  really was made with more than one tool. Reading "Claude" on 118 of 133
  cards is decoration, and a filter that cannot split anything is furniture.

## 0.8.0

The first release driven by an audit of a real library rather than a
feature list: 90 projects, ~37 added per month, three months of daily use.
It also carries everything from 0.7.0, which was built but never published.

### Categorization rewritten

Filing was wrong for roughly a fifth of the library and unhelpful for
another fifth. `_categorize` matched keywords as bare substrings and
returned the first category in dict order, so `'ai'` fired inside "wait"
and "airbnb", `'rl'` inside "ctrl", and `'ml '` inside "html ". Format
words decided subjects: a scalp-care routine filed under Finance because
the filename ended in "card", a job-application tracker under Health
because of "tracker".

- Keywords now match on whole-word boundaries, and ambiguous ones are
  phrases (`credit card`, `job application`, `real estate`).
- Every category is scored and the strongest signal wins, instead of the
  earliest dict key. Longer keywords and repeats both count for more.
- Fields are weighted by how much they're trusted to name the subject:
  path 3×, recorded intent 1.5×, body text 1×. Prose reaches for
  analogies the subject doesn't own; a health explainer written "with
  engineering analogies" is still health.
- The `intent` and `conceit` an artifact recorded about itself now feed
  the decision. They were sitting unused on 77 of 90 artifacts.
- Vocabulary rebuilt: format words (`tracker`, `guide`, `notes`, `card`,
  `review`, `story`, `explainer`) removed; domain terms added.

On the library that motivated this, clearly-misfiled projects went from 17
to 2 and the "Other" bucket from 17 to 4.

### `/craft` feedback loop

- `artifold designs --json --axes --limit N` returns just the rotation
  axes. Bare `--json` returned every row with its palette and flag block —
  ~68 KB read into context on every `/craft` invocation, growing with the
  library. The slim form is ~91% smaller and stays flat.
- `artifold:conceit` and `artifold:scale` are now parsed. `/craft` had been
  emitting both for months while `detect.py` dropped them, so no conceit
  ever reached the dashboard and the skill's own "intensity rotates too"
  rule had nothing to read. Both backfill on the next scan.
- Bundled `/craft` updated from three months of live use: a scale tier
  (`glance` / `read` / `experience`) chosen before any other rule, a
  content-editing step ahead of styling, and a CSS-first motion ladder in
  `references/motion.md` with reduced-motion and no-JS fail-safes.

### Project health

- Test suite grew from 2 files to 5 (48 tests), covering the categorizer,
  meta-tag extraction and the `designs` contract.
- GitHub Actions CI on Python 3.10–3.13, plus a build job that asserts the
  bundled skill actually ships inside the wheel.
- `pip install artifold[dev]` installs the test dependencies.

## 0.7.0

Built 2026-07-06, never published; folded into 0.8.0.

- Library intelligence: full-text `artifold search`, design fingerprints via
  `artifold designs`, and a version diff view in the dashboard.
- Grouping fix for date-prefixed slugs, so `2026-06-09-foo` and
  `2026-06-10-foo` collapse into one project with versions.
- Provenance lifecycle: entries carry forward across in-place edits and are
  marked superseded or orphaned instead of showing as `name: "?"`.
- The four-axis `/craft` skill ships inside the package
  (`artifold install-skill`).

## 0.6.2

- Card hover actions; defensive handling of malformed `data.json`.

## 0.6.1

- Trash button — move artifacts to the system Trash.

## 0.6.0

- PDF export: dashboard button, `artifold export-pdf`, and print CSS in
  `/craft`.

## 0.5.5

- Watcher robustness and a ~23× scan speedup by pruning skip-dirs during
  the walk instead of after it.

## 0.5.4

- Multi-file artifact support: sibling files and share bundling.

## 0.5.3

- `/craft` v2: design-mode and voice pickers, to fix output convergence.

## 0.5.2

- First public release.
