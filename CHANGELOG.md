# Changelog

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
