# Lessons

Patterns from corrections, so the same mistake does not happen twice.

## Check the ground truth before reasoning from a derived number

**What happened (2026-09-05):** I told the user they had shared 0 of 136
artifacts and built an argument on it ("this feature is for users who are not
you"). The number came from the provenance store. The share repo, which is
the ground truth, sat in `~/Library/Caches/artifold/share-repo/` with 11 live
pages in it. The store was wrong because of a bug.

**Rule:** before making a claim about the user's behavior from Artifold's own
records, check the source those records are derived from (the share repo,
the files on disk, `gh`). A surprising number in a derived store is more
likely a bug than a fact. One `ls` would have caught it.

## A running `artifold serve` keeps old code

**What happened:** after an upgrade, a long-running server kept writing
`data.json` with the old schema, which looked like a data regression. It also
means two servers (old and new) can race on the same store.

**Rule:** after changing Artifold code, restart any running `serve` before
measuring or judging behavior, and tell the user to restart theirs.

## Measure CPU time, not wall time, on this machine

Wall-clock timings of the same scan swung 4x between runs from background
load. Compare with `time.process_time()` medians, and compare against the
previous version on the same data in the same run.

- **A pipe hides a failed publish.** `uv publish ... | sed ... && git tag` tagged a release that had not uploaded, because the pipeline's exit code is sed's. The token in `.env` is `pypi_token`, so pass `UV_PUBLISH_TOKEN="$pypi_token"`. Check the upload line before tagging, or use `set -o pipefail`.

- **Taglines are where slop hides.** I wrote "Decks, reports and pages from AI that look designed, not generated. And one library that keeps every one of them." The user called it AI slop. The tells: an "X, not Y" line, an "And ..." fragment for rhythm, symmetry for its own sake ("each fixes the other"), and adjectives where a number or an example should go. Before shipping any opening copy, have a fresh-eyes subagent review it cold, the way craft reviews pages, and lead with a plain sentence that says what the thing is and who it is for.

- **Public demo runs must not see the real library.** Regenerating the gallery with `/craft` let the skill read the user's library, and two public pages came out addressed to the user by name with their employers' addresses. The old README screenshots had the same leak (real resume, visa and family pages). Run anything public against an isolated HOME: an `artifold` wrapper on PATH with `HOME=<empty demo home>`, as in `scripts/readme_shots.py`. Also: craft appends forged modes to the repo's `modes.md` through the skill symlink; check `git status artifold/skills` after any batch run.
- **Re-check a claim when the model under it changes.** "Ask Claude for a report and you get a purple gradient" was true of Opus 4.7 and false of Opus 5.5. Rerunning the gallery showed it; the copy had to follow the evidence.
