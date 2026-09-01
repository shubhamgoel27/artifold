"""Walk configured roots → group HTML files into project cards.

Heuristics (in order):
  1. Skip noise dirs (node_modules, .git, templates, …).
  2. Skip files buried deeper than max_depth (archives, repo dumps).
  3. Skip Django/Jinja server templates ({% ... %}).
  4. Skip dirs that are their own git repo (cloned code, not artifacts),
     unless explicitly listed in `allow_repos`.
  5. Within each project dir, group by *logical stem*. Files like
     `report-v2.html` and `report (1).html` collapse into one project
     with a `versions` array; export variants (`-print`, `-onepage`)
     attach to the matching bucket as `variants`.
  6. Attach per-file provenance (source URL, model, prompt, tool) by
     content hash, so metadata survives file moves/renames.
"""
from __future__ import annotations

import html
import os
import re
from pathlib import Path

from . import config, design, detect, intent, provenance

SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", "__pycache__",
             ".venv", "venv", "out", "coverage", ".cache", "artifold",
             "templates", "site-packages", ".tox", "migrations", "vendor"}

# Versions: `name-v2`, `name_v3`, `name (1)` at end of stem.
VERSION_END_RE = re.compile(r"^(.+?)[-_ ](?:v(\d+)|\((\d+)\))$", re.I)
# Date prefix from `artifold inbox` slugs (2026-06-09-dsa-bible). The date is
# provenance, not identity: two dated files with the same trailing slug are
# iterations of one project, so strip it before computing the logical stem.
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[-_ ]+")
# Variants: export forms (print/onepage/mobile/...) or `vN-` prefix.
VARIANT_RE = re.compile(
    r"(^|[-_])(print|printable|one[-_ ]?page|onepager|mobile|amp|draft|"
    r"slides?[-_]?print|export|pdf)([-_]|\.|$)|^v\d+[-_]", re.I)
TEMPLATE_RE = re.compile(r"\{%[-\s]")

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.I | re.S)
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    text = TAG_RE.sub(" ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


WORD_RE = re.compile(r"[a-z0-9]+")

# How much a field is trusted to say what an artifact is *about*. The path is
# the one field a human chose deliberately (and /craft writes it from the
# topic slug), so it dominates; the recorded intent comes next; body text is
# noisiest. Prose reaches for analogies the subject doesn't own — a health
# explainer "with engineering analogies" is still health, and a health plan
# that compares Airbnb's coverage is still a health plan. Weighting the path
# highest is what keeps `resume/resume.html` out of Engineering.
FIELD_WEIGHTS = {"name": 3.0, "intent": 1.5, "body": 1.0}


def _kw_weight(kw_tokens: list[str]) -> float:
    """Longer, more specific keywords count for more. A two-letter token
    like 'ml' is real signal but weak; 'infrastructure' is decisive."""
    n = sum(len(t) for t in kw_tokens)
    base = 1.0 if n <= 2 else 1.5 if n <= 4 else 2.5 if n <= 7 else 3.5
    return base + (1.0 if len(kw_tokens) > 1 else 0.0)   # phrases are specific


def _occurrences(tokens: list[str], kw_tokens: list[str]) -> int:
    """Count whole-word (or whole-phrase) hits of kw_tokens inside tokens."""
    n = len(kw_tokens)
    if not n or n > len(tokens):
        return 0
    return sum(1 for i in range(len(tokens) - n + 1)
               if tokens[i:i + n] == kw_tokens)


def _categorize(fields: dict[str, str], cats: dict[str, list[str]]) -> str:
    """Score every category over the weighted fields; best total wins.

    Was: first category in dict order containing any keyword as a bare
    substring. That filed 'ml engineer' under Engineering before Career's
    'resume' could be considered, and matched 'ai' inside "airbnb", 'rl'
    inside "ctrl". Now keywords match whole words, repeats and specificity
    both add weight, and the winner is the strongest signal rather than the
    earliest dict key.
    """
    toks = {f: WORD_RE.findall((fields.get(f) or "").lower())
            for f in FIELD_WEIGHTS}
    scores: dict[str, float] = {}
    for cat, kws in cats.items():
        total = 0.0
        for kw in kws:
            kw_tokens = WORD_RE.findall(kw.lower())
            if not kw_tokens:
                continue
            w = _kw_weight(kw_tokens)
            for field, fw in FIELD_WEIGHTS.items():
                hits = _occurrences(toks[field], kw_tokens)
                if hits:
                    # Repeats reinforce, with diminishing returns — a word
                    # said twice means it's the subject; ten times is a tic.
                    total += w * fw * (1 + 0.5 * min(hits - 1, 3))
        if total:
            scores[cat] = total
    if not scores:
        return "Other"
    best = max(scores.values())
    for cat in cats:                      # dict order breaks exact ties
        if scores.get(cat) == best:
            return cat
    return "Other"


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def _strip_date(stem: str) -> tuple[str, str]:
    """Return (date_str, stem_without_date_prefix). date_str = '' if none."""
    m = DATE_PREFIX_RE.match(stem)
    if not m:
        return "", stem
    rest = stem[m.end():]
    return (m.group(1), rest) if rest else ("", stem)


def _parse_version(stem: str) -> tuple[str, int]:
    """Return (logical_stem, version_number). Version 1 = no suffix."""
    m = VERSION_END_RE.match(stem)
    if not m:
        return stem, 1
    base = m.group(1)
    if m.group(2):           # -v2 style
        return base, int(m.group(2))
    return base, int(m.group(3)) + 1   # Chrome (1) = "second copy" → v2


def _classify(stem: str) -> tuple[str, str, int]:
    """('version'|'variant'|'main', base_stem, version_num)."""
    _date, logical = _strip_date(stem)
    base, v = _parse_version(logical)
    if v != 1:
        return "version", base, v
    if VARIANT_RE.search(logical):
        return "variant", logical, 1
    return "main", logical, 1


def _find_html(root: Path, max_depth: int):
    """Walk `root`, pruning SKIP_DIRS at the *directory* level (so we never
    descend into .venv/node_modules/.git/etc.) and capping at max_depth.
    Yields HTML files past the Django/Jinja template-tag filter.

    Was: rglob('*.html') + post-filter — walks EVERY dir under root then
    discards. On ~/work that means walking 45,000+ dirs (most inside
    .venv/node_modules/etc.) only to throw them away. ~10x slowdown.

    Now: os.scandir-based recursion that skips SKIP_DIRS before descending,
    cutting the walk to the dirs that could plausibly contain artifacts.
    """
    def walk(d: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = list(os.scandir(d))
        except (PermissionError, OSError):
            return
        for e in entries:
            try:
                is_dir = e.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if is_dir:
                if e.name in SKIP_DIRS:
                    continue
                yield from walk(e.path, depth + 1)
                continue
            if not e.name.lower().endswith(".html"):
                continue
            p = Path(e.path)
            try:
                head = p.read_text(encoding="utf-8", errors="ignore")[:4000]
            except Exception:
                continue
            if TEMPLATE_RE.search(head):
                continue
            yield p
    yield from walk(str(root), 1)


def _extract_meta(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raw = ""
    head = raw[:60000]
    title = _clean(TITLE_RE.search(head).group(1)) if TITLE_RE.search(head) else ""
    heading = _clean(H_RE.search(head).group(1)) if H_RE.search(head) else ""
    snippet = ""
    for m in P_RE.finditer(raw[:120000]):
        c = _clean(m.group(1))
        if len(c) > 40:
            snippet = c[:240]
            break
    st = path.stat()
    return {
        "title": title or heading or path.stem.replace("-", " ").title(),
        "heading": heading,
        "snippet": snippet,
        "mtime": st.st_mtime,
        "size": st.st_size,
    }


def _common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _prov_for(f: Path) -> tuple[str | None, dict | None]:
    try:
        sha = provenance.sha1_of(f)
    except Exception:
        return None, None
    entry = provenance.get(sha)
    if entry is None:
        # In-place edit: same path, new content hash. Migrate the metadata.
        entry = provenance.carry_forward(sha, f)
    return sha, entry


def _enrich_provenance(f: Path, sha: str, entry: dict | None) -> dict | None:
    """Run zero-cost enrichment on a file: embedded artifold:* meta tags,
    source fingerprinting, and lightweight design extraction.
    User-asserted tool/intent fields are preserved."""
    entry = entry or {}
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return entry

    fields: dict = {}

    # 1. embedded artifold:* meta tags (strongest signal). Re-extract even
    # for already-enriched entries so newly-recognised tags backfill on the
    # next scan, but never clobber a field the user set by hand.
    embedded = detect.extract_embedded_meta(content)
    if embedded:
        if entry.get("intent_source") == "user":
            embedded = {k: v for k, v in embedded.items() if k not in entry}
        if embedded:
            fields.update(embedded)
            if entry.get("intent_source") != "user":
                fields["intent_source"] = "embedded"

    # 2. source-tool fingerprinting from HTML markers
    if not fields.get("tool") and not entry.get("tool"):
        t = detect.detect_tool(content)
        if t:
            fields["tool"] = t
            fields["detection_source"] = "auto"

    # 3. design fingerprint (always recompute — cheap, reflects current file)
    try:
        fields["design"] = design.extract(content)
    except Exception:
        pass

    # 4. remember where this content lives so carry_forward() can find the
    # entry after an in-place edit changes the hash
    if entry.get("path") != str(f):
        fields["path"] = str(f)

    if not fields:
        return entry
    return provenance.set_(sha, **fields)


def _body_text(path: Path) -> str:
    """Plain-text body of an HTML file, lightweight (no parser dep)."""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    return _clean(raw)[:4000]


def _scan_root(root: Path, cfg: dict, cats: dict,
               intent_jobs: dict[str, tuple[str, str, Path]]) -> list[dict]:
    """Scan one root; mutates `intent_jobs` with (sha → (title, body, file))
    entries that need LLM inference (queued for the caller to batch)."""
    root = root.resolve()
    allow = set(cfg.get("allow_repos") or [])
    max_depth = int(cfg.get("max_depth") or 3)
    root_slug = _slugify(root.name) or "root"
    intent_on = intent.enabled(cfg)

    # Top-level files share ONE group per root (was: one group per file,
    # which meant `report.html` + `report-v2.html` at root level, and any
    # two date-prefixed inbox iterations, could never collapse into
    # versions of the same project).
    groups: dict[str, list[Path]] = {}
    for p in _find_html(root, max_depth):
        rel = p.relative_to(root)
        key = rel.parts[0] if len(rel.parts) > 1 else "__top__"
        if (key != "__top__" and key not in allow
                and (root / key / ".git").is_dir()):
            continue
        groups.setdefault(key, []).append(p)

    projects: list[dict] = []
    for dir_key, files in groups.items():
        files.sort()
        metas = {f: _extract_meta(f) for f in files}

        # Bucket mains+versions by logical stem; collect variants for attach.
        buckets: dict[str, list[tuple[Path, int]]] = {}   # base -> [(file, ver)]
        variants_loose: list[Path] = []
        for f in files:
            kind, base, ver = _classify(f.stem)
            if kind == "variant":
                variants_loose.append(f)
            else:
                buckets.setdefault(base, []).append((f, ver))

        if not buckets:                       # all files were variants
            f = variants_loose.pop(0)
            buckets[_strip_date(f.stem)[1]] = [(f, 1)]

        # Attach loose variants to bucket with the longest stem-prefix match.
        # Compare date-stripped stems so `2026-06-12-foo-print` matches `foo`.
        attach_v: dict[str, list[Path]] = {b: [] for b in buckets}
        for v in variants_loose:
            v_logical = _strip_date(v.stem)[1].lower()
            best = max(buckets, key=lambda b: _common_prefix(b.lower(), v_logical))
            attach_v[best].append(v)

        single_bucket = len(buckets) == 1 and dir_key != "__top__"

        for base, version_pairs in buckets.items():
            # Same-slug iterations (dated inbox files) all parse as v1:
            # renumber duplicates chronologically (filename date, then mtime)
            # so v1 is the oldest and the newest wins primary.
            if len({v for _, v in version_pairs}) < len(version_pairs):
                version_pairs.sort(
                    key=lambda fp: (_strip_date(fp[0].stem)[0],
                                    metas[fp[0]]["mtime"]))
                version_pairs = [(f, i + 1)
                                 for i, (f, _) in enumerate(version_pairs)]
            # Sort versions descending (highest version first; mtime tiebreak)
            version_pairs.sort(key=lambda fp: (fp[1], metas[fp[0]]["mtime"]),
                               reverse=True)
            primary, primary_v = version_pairs[0]
            attached_variants = attach_v[base]
            all_files = [f for f, _ in version_pairs] + attached_variants

            if dir_key == "__top__":
                proj_dir = primary.parent.relative_to(root).as_posix() or "."
            else:
                proj_dir = dir_key
            proj_name = (metas[primary]["title"]
                         or primary.stem.replace("-", " ").replace("_", " ").title())
            uid = f"{root_slug}/{dir_key}" if single_bucket else f"{root_slug}/{dir_key}/{base}"

            primary_sha, primary_prov = _prov_for(primary)
            if primary_sha:
                primary_prov = _enrich_provenance(primary, primary_sha, primary_prov)
                if intent_on and primary_sha not in intent_jobs and (
                        not primary_prov or not primary_prov.get("intent")):
                    intent_jobs[primary_sha] = (
                        metas[primary]["title"], _body_text(primary), primary)

            # Categorization fields, weighted by how much each is trusted to
            # say what the artifact is *about*. `intent` and `conceit` are
            # written by the generator itself and are the sharpest topic
            # signal we have — 77 of 90 artifacts in a real library carry one.
            revisions = provenance.chain_for(primary_sha) if primary_sha else []

            _pp = primary_prov or {}
            cat_fields = {
                # dir_key alone stopped carrying the name signal once
                # top-level files shared one group; the stem restores it.
                "name":   f"{dir_key} {primary.stem}",
                "intent": f"{_pp.get('intent') or ''} {_pp.get('conceit') or ''}",
                "body":   f"{metas[primary]['title']} {metas[primary]['heading']}",
            }

            versions_payload = []
            for f, vn in version_pairs:
                sha, p = _prov_for(f)
                if sha:
                    p = _enrich_provenance(f, sha, p)
                    if intent_on and sha not in intent_jobs and (
                            not p or not p.get("intent")):
                        intent_jobs[sha] = (metas[f]["title"], _body_text(f), f)
                versions_payload.append({
                    "path": f.resolve().as_posix(),
                    "rel": f.relative_to(root).as_posix(),
                    "title": metas[f]["title"],
                    "mtime": metas[f]["mtime"],
                    "version": vn,
                    "sha1": sha,
                    "provenance": p,
                })

            projects.append({
                "id": _slugify(uid),
                "name": proj_name,
                "dir": proj_dir,
                "root": str(root),
                "category": _categorize(cat_fields, cats),
                "primary": {
                    "path": primary.resolve().as_posix(),
                    "rel": primary.relative_to(root).as_posix(),
                    "sha1": primary_sha,
                    "provenance": primary_prov,
                    **{k: metas[primary][k]
                       for k in ("title", "heading", "snippet", "mtime")},
                },
                "versions": versions_payload,        # newest → oldest
                "version_count": len(versions_payload),
                "current_version": primary_v,
                # In-place edit history, distinct from filename versions.
                # `-v2`/`(1)` filenames match ~2% of a real library; editing
                # a file in place is what actually happens, and the chain
                # records it. Revisions carry no content, so they cannot be
                # diffed — they say the artifact changed, and when.
                "revisions": revisions,
                "revision_count": len(revisions),
                "open_count": int(primary_prov.get("open_count") or 0)
                              if primary_prov else 0,
                "last_opened_at": (primary_prov or {}).get("last_opened_at"),
                "variants": [
                    {
                        "path": f.resolve().as_posix(),
                        "rel": f.relative_to(root).as_posix(),
                        "title": metas[f]["title"],
                        "mtime": metas[f]["mtime"],
                    }
                    for f in attached_variants
                ],
                "file_count": len(all_files),
                "latest_mtime": max(metas[f]["mtime"] for f in all_files),
                "search_text": " ".join(
                    f"{metas[f]['title']} {metas[f]['heading']} {metas[f]['snippet']}"
                    for f in all_files).lower(),
            })

    return projects


def scan_all(roots: list[Path] | None = None,
             intent_override: bool | None = None) -> list[dict]:
    cfg = config.load()
    if intent_override is not None:           # CLI flag wins over config
        cfg = {**cfg, "enable_intent": intent_override}
    cats = config.categories(cfg)
    full_scan = roots is None                 # partial scans must not GC
    roots = roots if roots is not None else config.roots()

    intent_jobs: dict[str, tuple[str, str, Path]] = {}
    out: list[dict] = []
    for r in roots:
        if not r.is_dir():
            print(f"  ! root does not exist, skipping: {r}")
            continue
        out.extend(_scan_root(r, cfg, cats, intent_jobs))

    # Batch the LLM calls *after* walking everything, so any embedded-meta
    # provenance set during enrichment already shows up.
    if intent.enabled(cfg) and intent_jobs:
        items = [(sha, t, b) for sha, (t, b, _f) in intent_jobs.items()]
        results = intent.infer_many_sync(
            items,
            model=cfg.get("intent_model") or intent.DEFAULT_MODEL,
            concurrency=int(cfg.get("intent_concurrency") or 5))
        for sha, fields in results.items():
            provenance.set_(sha, intent_source="inferred", **fields)
        # Re-attach provenance to project payload (it may have changed).
        for proj in out:
            psha = proj["primary"].get("sha1")
            if psha:
                proj["primary"]["provenance"] = provenance.get(psha)
            for v in proj.get("versions") or []:
                if v.get("sha1"):
                    v["provenance"] = provenance.get(v["sha1"])

    # Reconcile the provenance store against what this scan actually saw:
    # unseen entries get orphan-stamped and eventually dropped (they'd
    # otherwise surface as name:"?" rows in `artifold designs` forever).
    if full_scan:
        active = {v.get("sha1")
                  for proj in out
                  for v in [proj["primary"], *(proj.get("versions") or [])]
                  if v.get("sha1")}
        provenance.gc(active)

    out.sort(key=lambda p: p["latest_mtime"], reverse=True)
    return out
