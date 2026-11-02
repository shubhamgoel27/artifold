# Artifold

Two parts that ship as one package:

- **craft**, a design skill for Claude Code and Codex: `artifold/skills/craft/` (SKILL.md plus `references/`). On this machine `~/.claude/skills/craft` is a symlink to that folder, so edits take effect in every session at once.
- **Artifold**, a local library and dashboard for HTML pages: the `artifold/` Python package. `scan.py` finds pages, `provenance.py` stores what is known about each one (keyed by content hash), `serve.py` runs the dashboard with a file watcher, `template.html` is the whole dashboard UI.

`tasks/lessons.md` holds past mistakes and the rules that came from them. Read it before release work or anything touching the watcher, sharing, or the gallery.

## Test

```bash
.venv/bin/python -m pytest -q        # about half a second, no browser needed
```

After editing the skill, `tests/test_skill_refs.py` checks that every reference it names exists. A Linux-only watcher test skips on macOS; CI runs it.

For UI changes, check the real page in a browser at 390, 600 and 1400 px wide. Build the test library with the helpers in `scripts/readme_shots.py` (`build_library`, `setup_home`, `env_for`) so the run never sees the real library.

## Release

1. Tests pass. Bump `__version__` in `artifold/__init__.py` and `"version"` in `.claude-plugin/plugin.json` (a test checks they match). Add a CHANGELOG entry in the existing style.
2. Commit, push, and wait for CI: `gh run list --workflow=ci --commit <sha>`, then `gh run watch <id> --exit-status`.
3. Build from a clean export, never the working tree: `git archive HEAD | tar -x -C <tmp>`, then `uv build --out-dir dist` from there.
4. `uvx --python 3.12 twine check dist/*<version>*`. Without `--python 3.12`, uvx can pick the system Python 3.9 and an old twine that rejects metadata 2.5.
5. Publish with `set -o pipefail`, the token from `.env` (variable `pypi_token`, passed as `UV_PUBLISH_TOKEN`), and the output piped through a filter that hides `pypi-…` strings. Never print the token. Check the upload lines before tagging.
6. Tag `v<version>` and push the tag. PyPI's JSON can lag a minute; `https://pypi.org/pypi/artifold/<version>/json` answers first.
7. Restart any running `artifold serve`. It rescans once at startup, which rebuilds the dashboard page from the new template.

Ask before publishing when someone else is verifying the commit first (for example the home-server session).

## Rules that are easy to break

- **Public output never sees the real library, or anything personal.** The gallery, README screenshots and demo GIF are made against an empty library: put a wrapper first on PATH that runs `HOME=<empty demo home> .venv/bin/artifold "$@"`. That is not enough on its own: a session still knows the account's name and can read any file on disk. One run found the author's interview notes in `~/work` and wrote them into the page. End gallery prompts with the public-gallery note in `scripts/build_gallery.py`, and grep every page for names and employers before it goes in `docs/`.
- **craft edits its own catalog.** Runs can append invented modes to `references/modes.md` through the symlink. After any batch of craft runs, check `git status artifold/skills` and revert what you did not mean to keep.
- **The watcher reacts only to changes.** Linux reports reads as events; reacting to them made every scan trigger the next (fixed in 0.17.1, guarded by `tests/test_watcher.py`).
- **Responsive CSS goes at the end of `template.html`.** A phone rule placed above the base rule it overrides never applies (guarded by `tests/test_template_layout.py`).
- **Claims follow the evidence.** The README and gallery say what the current model and skill actually produce. When the model changes, rerun before repeating an old claim.

## Writing

README, CHANGELOG and page copy: plain, concrete English, no em dashes, no buzzwords, no "X, not Y" taglines. Have a fresh-eyes subagent read any opening copy cold before it goes out.
