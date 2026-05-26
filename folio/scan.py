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
import re
from pathlib import Path

from . import config, design, detect, intent, provenance

SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", "__pycache__",
             ".venv", "venv", "out", "coverage", ".cache", "folio",
             "templates", "site-packages", ".tox", "migrations", "vendor"}

# Versions: `name-v2`, `name_v3`, `name (1)` at end of stem.
VERSION_END_RE = re.compile(r"^(.+?)[-_ ](?:v(\d+)|\((\d+)\))$", re.I)
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


def _categorize(haystack: str, cats: dict[str, list[str]]) -> str:
    h = haystack.lower()
    for cat, kws in cats.items():
        if any(k in h for k in kws):
            return cat
    return "Other"


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


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
    base, v = _parse_version(stem)
    if v != 1:
        return "version", base, v
    if VARIANT_RE.search(stem):
        return "variant", stem, 1
    return "main", stem, 1


def _find_html(root: Path, max_depth: int):
    for p in root.rglob("*.html"):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if len(rel.parts) > max_depth:
            continue
        try:
            head = p.read_text(encoding="utf-8", errors="ignore")[:4000]
        except Exception:
            continue
        if TEMPLATE_RE.search(head):
            continue
        yield p


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
    return sha, provenance.get(sha)


def _enrich_provenance(f: Path, sha: str, entry: dict | None) -> dict | None:
    """Run zero-cost enrichment on a file: embedded folio:* meta tags,
    source fingerprinting, and lightweight design extraction.
    User-asserted tool/intent fields are preserved."""
    entry = entry or {}
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return entry

    fields: dict = {}

    # 1. embedded folio:* meta tags (strongest signal)
    if not (entry.get("tool") and entry.get("intent_source") in ("user", "embedded")):
        embedded = detect.extract_embedded_meta(content)
        if embedded:
            fields.update(embedded)
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

    groups: dict[str, list[Path]] = {}
    for p in _find_html(root, max_depth):
        rel = p.relative_to(root)
        key = rel.parts[0] if len(rel.parts) > 1 else f"__top__/{rel.name}"
        if (not key.startswith("__top__/") and key not in allow
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
            buckets[f.stem] = [(f, 1)]

        # Attach loose variants to bucket with the longest stem-prefix match.
        attach_v: dict[str, list[Path]] = {b: [] for b in buckets}
        for v in variants_loose:
            best = max(buckets, key=lambda b: _common_prefix(b.lower(), v.stem.lower()))
            attach_v[best].append(v)

        single_bucket = len(buckets) == 1

        for base, version_pairs in buckets.items():
            # Sort versions descending (highest version first; mtime tiebreak)
            version_pairs.sort(key=lambda fp: (fp[1], metas[fp[0]]["mtime"]),
                               reverse=True)
            primary, primary_v = version_pairs[0]
            attached_variants = attach_v[base]
            all_files = [f for f, _ in version_pairs] + attached_variants

            if dir_key.startswith("__top__/"):
                proj_dir = primary.parent.relative_to(root).as_posix() or "."
            else:
                proj_dir = dir_key
            proj_name = (metas[primary]["title"]
                         or primary.stem.replace("-", " ").replace("_", " ").title())
            haystack = f"{dir_key} {metas[primary]['title']} {metas[primary]['heading']}"
            uid = f"{root_slug}/{dir_key}" if single_bucket else f"{root_slug}/{dir_key}/{base}"

            primary_sha, primary_prov = _prov_for(primary)
            if primary_sha:
                primary_prov = _enrich_provenance(primary, primary_sha, primary_prov)
                if intent_on and primary_sha not in intent_jobs and (
                        not primary_prov or not primary_prov.get("intent")):
                    intent_jobs[primary_sha] = (
                        metas[primary]["title"], _body_text(primary), primary)

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
                "category": _categorize(haystack, cats),
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

    out.sort(key=lambda p: p["latest_mtime"], reverse=True)
    return out
