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
