# Rename: folio → artifold

## Order of operations
1. Stop the running folio serve (if any)
2. Mv local dir: ~/work/folio → ~/work/artifold
3. Code changes (find/replace):
   - `folio` (lowercase, word boundary) → `artifold`
   - `Folio` (titlecase) → `Artifold`
   - `ai-folio` (pypi name) → `artifold`
   - `folio-share` → `artifold-share`
   - `folio-inbox` (in defaults only) → `artifold-inbox`
   - `'folio-theme'` (localStorage) → `'artifold-theme'`
4. Rename inner package dir: artifold/folio → artifold/artifold
5. Update pyproject.toml: name=artifold, console script=artifold, package=artifold
6. Reinstall locally: `uv tool install --editable .`
7. Migrate user data:
   - mv ~/Library/Application Support/folio → ~/Library/Application Support/artifold
   - mv ~/Library/Caches/folio → ~/Library/Caches/artifold
   - mv ~/folio-inbox → ~/artifold-inbox (optional)
   - update config drop_dir + roots
8. Verify: `artifold --version` + `artifold scan` runs clean
9. GitHub:
   - Rename `shubhamgoel27/folio` → `shubhamgoel27/artifold`
   - Rename `shubhamgoel27/folio-share` → `shubhamgoel27/artifold-share`
10. Update remote: `git remote set-url origin ...`
11. Force-push (optional, since rename auto-redirects)
12. Re-record demo with new branding + new share URL
13. Update PyPI publish plan (next chunk)

## Things to verify after
- artifold --help shows artifold (not folio) everywhere
- artifold doctor runs clean
- artifold scan picks up existing artifacts (cache migrated)
- artifold serve opens at correct URL
- artifold install-skill copies the right SKILL.md
- Skill references `artifold inbox/designs/info` (not `folio ...`)
- Dashboard header says "Artifold" not "Folio"
- localStorage theme key migrated (or just accept users re-pick theme)

## Dead URLs we accept
- shubhamgoel27.github.io/folio-share/* — all old shares 404
- The dobble demo URL we sent for testing
- README screenshots with "Folio" wordmark need re-shoot
- Demo GIF with "Folio" wordmark needs re-record
