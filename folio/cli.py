"""Folio CLI.

Subcommands:
    folio init                    create config dir
    folio add <dir>               add a root to scan
    folio remove <dir>            remove a root
    folio roots                   list configured roots
    folio scan                    scan + screenshot + build (one-shot)
    folio serve [--port N]        live dashboard with auto-rescan
    folio open                    print the dashboard URL / file
    folio                         default: serve + open the browser
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import webbrowser
from pathlib import Path

from . import __version__, config, provenance
from .paths import CONFIG_DIR, CONFIG_FILE, INDEX, ensure_dirs


def _count_html(p: Path, max_count: int = 9999) -> int:
    n = 0
    try:
        for _ in p.rglob("*.html"):
            n += 1
            if n >= max_count:
                break
    except Exception:
        pass
    return n


def _is_tty() -> bool:
    import sys
    return sys.stdin.isatty() and sys.stdout.isatty()


def _cmd_init(args):
    ensure_dirs()
    if not CONFIG_FILE.exists():
        config.save(dict(config.DEFAULTS))

    print(f"\n  📚  Folio — local library for your AI-generated artifacts\n")
    print(f"  config: {CONFIG_FILE}\n")

    if args.non_interactive or not _is_tty():
        print("  (non-interactive — skipping wizard. next: `folio add <dir>`)")
        return 0

    cfg = config.load()
    existing = cfg.get("roots") or []
    if existing:
        print(f"  Already configured roots:")
        for r in existing:
            print(f"    · {r}")
        print()
        ans = input("  Add another? [y/N]: ").strip().lower()
        if ans in ("y", "yes"):
            _wizard_pick_root(existing)
    else:
        _wizard_pick_root(existing)

    cfg = config.load()
    if not (cfg.get("roots") or []):
        print("\n  Nothing scanned yet. Add a root any time: folio add <dir>")
        return 0

    ans = input("\n  Run an initial scan now? (~30s + chromium download on first run) [Y/n]: ").strip().lower()
    if ans in ("n", "no"):
        print("  ok — run `folio scan` when ready.")
        return 0

    from . import scan, shoot, build
    import asyncio
    rs = config.roots()
    print()
    projects = scan.scan_all()
    print(f"  found {len(projects)} project(s) "
          f"({sum(p['file_count'] for p in projects)} html files)")
    asyncio.run(shoot.shoot(projects))
    build.build(projects, [str(r) for r in rs])

    if input("\n  Open the dashboard? [Y/n]: ").strip().lower() not in ("n", "no"):
        return _cmd_open(None)
    print("\n  done. run `folio` any time to view + auto-rescan.")
    return 0


def _wizard_pick_root(existing: list[str]):
    existing_set = {str(Path(r).expanduser().resolve()) for r in existing}
    candidates = [Path.home() / d for d in ("Downloads", "Documents", "Desktop")]
    candidates = [c for c in candidates
                  if c.is_dir() and str(c) not in existing_set]
    if candidates:
        print("\n  Common places AI-generated HTML lands:")
        for i, c in enumerate(candidates, 1):
            n = _count_html(c, 200)
            note = f"~{n} html files" if n < 200 else "200+ html files"
            print(f"    {i}. {c}   ({note})")
        print(f"    {len(candidates)+1}. enter a custom path")
        print(f"    {len(candidates)+2}. skip — add later")
        choice = input(f"\n  Pick [1-{len(candidates)+2}]: ").strip()
        if not choice.isdigit():
            return
        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            ok, msg = config.add_root(candidates[idx])
            print(f"    {'added' if ok else '!'} {msg}")
            return
        if idx == len(candidates):
            _wizard_custom_path()
        return
    _wizard_custom_path()


def _wizard_custom_path():
    p = input("  Path to scan: ").strip()
    if not p:
        return
    ok, msg = config.add_root(p)
    print(f"    {'added' if ok else '!'} {msg}")


def _cmd_add(args):
    ok, msg = config.add_root(args.path)
    print(("added: " if ok else "! ") + msg)
    return 0 if ok else 1


def _cmd_remove(args):
    ok, msg = config.remove_root(args.path)
    print(("removed: " if ok else "! ") + msg)
    return 0 if ok else 1


def _cmd_roots(_args):
    rs = config.load().get("roots") or []
    if not rs:
        print("(no roots configured)  run: folio add <dir>")
        return
    for r in rs:
        print(r)


def _cmd_scan(args):
    from . import scan, shoot, build
    rs = config.roots()
    if not rs:
        print("! no roots configured. run: folio add <dir>")
        return 1
    intent_override = True if args.intent else (False if args.no_intent else None)
    if args.intent:                       # explicit opt-in: explain if we'll skip
        from . import intent as _intent
        try:
            import anthropic  # noqa: F401
        except ImportError:
            print("  ! --intent: extra not installed. run: pip install 'ai-folio[intent]'")
            intent_override = False
        else:
            if not _intent.have_api_key():
                print("  ! --intent: ANTHROPIC_API_KEY not set; intent will be skipped")
                intent_override = False
    print(f"scanning {len(rs)} root(s)…")
    projects = scan.scan_all(intent_override=intent_override)
    print(f"  found {len(projects)} projects "
          f"({sum(p['file_count'] for p in projects)} html files)")
    if args.no_shoot:
        cached = shoot.resolve_cached_thumbs(projects)
        kept = len(projects) - len(cached)
        print(f"  --no-shoot: reused {kept} cached thumbnails, "
              f"{len(cached)} without preview")
    else:
        asyncio.run(shoot.shoot(projects, args.concurrency))
    build.build(projects, [str(r) for r in rs])
    print("done.")


def _cmd_serve(args):
    from . import serve as serve_mod
    serve_mod.serve(port=args.port, open_browser=not args.no_open)


def _cmd_open(_args):
    if not INDEX.exists():
        print("! no dashboard built yet. run: folio scan")
        return 1
    url = INDEX.as_uri()
    print(url)
    webbrowser.open(url)


def _cmd_designs(args):
    """List or dump design fingerprints. Designs are extracted at scan time,
    cached in the provenance store, keyed by content SHA1."""
    from . import design, provenance
    from .paths import DATA
    import json

    # Build a lookup: short sha → (path, project) using the latest scan.
    by_sha: dict[str, dict] = {}
    if DATA.exists():
        d = json.loads(DATA.read_text())
        for proj in d.get("projects") or []:
            for v in proj.get("versions") or [proj.get("primary")]:
                sha = (v or {}).get("sha1")
                if sha:
                    by_sha[sha] = {"path": v["path"], "name": proj["name"],
                                    "dir": proj["dir"], "version": v.get("version", 1)}

    if not args.id:
        # list mode
        items = provenance.all_items()
        rows = []
        for sha, entry in items.items():
            d = entry.get("design") or {}
            if not d:
                continue
            info = by_sha.get(sha, {})
            name = info.get("name", "?")
            sig = []
            if d.get("themed"):   sig.append("themed")
            if d.get("gradient"): sig.append("gradient")
            if d.get("glass"):    sig.append("glass")
            if d.get("animated"): sig.append("anim")
            pal = " ".join(d.get("palette", [])[:4])
            rows.append((sha[:8], name[:38], pal, " ".join(sig)))
        if not rows:
            print("(no design fingerprints yet — run `folio scan`)")
            return 0
        print(f"  {'id':<10}{'name':<40}{'palette':<28}flags")
        for r in rows[:60]:
            print(f"  {r[0]:<10}{r[1]:<40}{r[2]:<28}{r[3]}")
        return 0

    # single-artifact mode
    target_sha = next((s for s in provenance.all_items()
                       if s.startswith(args.id)), None)
    if not target_sha:
        print(f"  ! no artifact found with id starting {args.id!r}")
        print(f"    run `folio designs` to list available ids")
        return 1
    info = by_sha.get(target_sha, {})
    if args.template or args.css or args.skeleton:
        if not info.get("path"):
            print(f"  ! no current file path for {target_sha[:8]} "
                  f"— run `folio scan` first")
            return 1
        html = Path(info["path"]).read_text(encoding="utf-8", errors="ignore")
        if args.css:
            for s in design.STYLE_RE.findall(html):
                print(s.strip())
        elif args.skeleton:
            print(design.as_template(html, include_css=False, include_skeleton=True))
        else:  # --template (default for single-id mode with body flags)
            print(design.as_template(html))
        return 0
    # default: print the fingerprint as JSON
    entry = provenance.get(target_sha) or {}
    d = entry.get("design") or {}
    print(json.dumps({"sha1": target_sha, **info, **d}, indent=2))
    return 0


def _cmd_install_skill(args):
    """Copy the bundled /craft Claude Code skill into ~/.claude/skills/."""
    from importlib import resources
    src = resources.files("folio.skills.craft").joinpath("SKILL.md")
    dest_dir = Path(args.dest).expanduser() if args.dest else \
               Path.home() / ".claude" / "skills" / "craft"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    if dest.exists() and not args.force:
        print(f"  ! already installed at {dest}")
        print(f"    pass --force to overwrite")
        return 1
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  installed /craft skill → {dest}")
    print()
    print("  Try it in Claude Code:")
    print("    /craft a 30-day strength tracker for a beginner")
    print("    /craft a one-pager comparing SF apartments")
    print("    /craft an explainer of how transformers work, like dobble")
    print()
    print("  The skill will consult your Folio library for style references")
    print("  by default; pass a reference explicitly with `like <id-or-name>`.")
    return 0


def _cmd_inbox(args):
    """Print the canonical path for a new artifact (date-prefixed slug).

    Used by the /craft skill (and humans) to keep all generated artifacts
    in one place with sortable filenames. Auto-creates ~/folio-inbox/
    and adds it as a root the first time it's needed.
    """
    import re
    from datetime import datetime
    cfg = config.load()
    if cfg.get("drop_dir"):
        inbox = Path(cfg["drop_dir"]).expanduser().resolve()
    else:
        inbox = (Path.home() / "folio-inbox").resolve()
    inbox.mkdir(parents=True, exist_ok=True)
    # Ensure inbox is a watched root (so the artifact auto-indexes when written)
    roots = [str(Path(r).expanduser().resolve()) for r in (cfg.get("roots") or [])]
    if str(inbox) not in roots:
        config.add_root(inbox)
        fresh = config.load()
        if not fresh.get("drop_dir"):
            fresh["drop_dir"] = str(inbox)
            config.save(fresh)
    topic = " ".join(args.topic) if args.topic else "untitled"
    slug = re.sub(r"[^\w\s-]", "", topic.lower()).strip()
    slug = re.sub(r"\s+", "-", slug)[:60].strip("-") or "untitled"
    date = datetime.now().strftime("%Y-%m-%d")
    path = inbox / f"{date}-{slug}.html"
    # Disambiguate if a file with that exact name already exists today
    i = 2
    while path.exists():
        path = inbox / f"{date}-{slug}-{i}.html"
        i += 1
    print(path)
    return 0


def _cmd_doctor(_args):
    from . import diagnostics
    print(f"Folio diagnostics (config: {diagnostics.CONFIG_FILE})\n")
    checks = diagnostics.run_all()
    fails, warns = diagnostics.report(checks)
    print()
    if fails == 0 and warns == 0:
        print("all good ✓")
        return 0
    print(f"{fails} blocker(s), {warns} warning(s).")
    return 0 if fails == 0 else 1


def _cmd_share(args):
    from . import share
    if args.list:
        items = share.list_shares()
        if not items:
            print("(no shares yet)")
            return 0
        for it in items:
            print(f"  {it['id']}  {it['url']}")
            if it.get("source"):
                print(f"           src: {it['source']}")
        return 0
    if args.revoke:
        return 0 if share.revoke(args.revoke) else 1
    if not args.file:
        print("! pass a file to share, or --list / --revoke <id>")
        return 1
    url = share.share_via_gh(Path(args.file), no_clipboard=args.no_clipboard)
    return 0 if url else 1


def _cmd_import(args):
    from . import importer
    out = importer.import_url(args.url, name=args.name, drop_dir=args.drop_dir)
    return 0 if out else 1


def _cmd_link(args):
    """Attach provenance (source URL / tool / model / prompt) to a file."""
    p = Path(args.file).expanduser().resolve()
    if not p.is_file():
        print(f"! not a file: {p}")
        return 1
    fields = {k: v for k, v in {
        "source": args.source, "tool": args.tool,
        "model": args.model, "prompt": args.prompt,
        "notes": args.note,
    }.items() if v}
    if args.tag:
        fields["tags"] = list(args.tag)
    if not fields:
        print("! nothing to set — pass at least one of --source/--tool/"
              "--model/--prompt/--tag/--note")
        return 1
    try:
        sha, entry = provenance.annotate_path(p, **fields)
    except ValueError as e:
        print(f"! {e}")
        return 1
    print(f"linked {p}")
    print(f"  sha1: {sha}")
    for k in ("source", "tool", "model", "tags", "prompt", "notes"):
        if entry.get(k):
            v = entry[k]
            if isinstance(v, str) and len(v) > 80:
                v = v[:77] + "…"
            print(f"  {k}: {v}")


def _cmd_info(args):
    """Show provenance + project info for a file."""
    p = Path(args.file).expanduser().resolve()
    if not p.is_file():
        print(f"! not a file: {p}")
        return 1
    sha = provenance.sha1_of(p)
    entry = provenance.get(sha)
    print(f"file:    {p}")
    print(f"sha1:    {sha}")
    if not entry:
        print("(no provenance attached — run `folio link <file> ...`)")
        return 0
    for k in ("source", "tool", "model", "tags", "prompt", "notes", "added_at"):
        if entry.get(k) is not None:
            print(f"{k+':':9}{entry[k]}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="folio",
        description="Local-first library for your AI-generated HTML artifacts.")
    p.add_argument("--version", action="version", version=f"folio {__version__}")
    sub = p.add_subparsers(dest="cmd")

    init_p = sub.add_parser("init", help="initialize Folio (interactive wizard)")
    init_p.add_argument("--non-interactive", action="store_true",
                        help="skip prompts; just create the config dir")
    init_p.set_defaults(fn=_cmd_init)

    a = sub.add_parser("add", help="add a root directory")
    a.add_argument("path"); a.set_defaults(fn=_cmd_add)

    r = sub.add_parser("remove", help="remove a root directory")
    r.add_argument("path"); r.set_defaults(fn=_cmd_remove)

    sub.add_parser("roots", help="list configured roots").set_defaults(fn=_cmd_roots)

    s = sub.add_parser("scan", help="scan + screenshot + build dashboard")
    s.add_argument("--no-shoot", action="store_true",
                   help="skip screenshots; reuse cached thumbnails")
    s.add_argument("--concurrency", type=int, default=5)
    g = s.add_mutually_exclusive_group()
    g.add_argument("--intent", action="store_true",
                   help="force-enable LLM intent inference for this run "
                        "(needs ANTHROPIC_API_KEY)")
    g.add_argument("--no-intent", action="store_true",
                   help="force-skip LLM intent inference for this run")
    s.set_defaults(fn=_cmd_scan)

    v = sub.add_parser("serve", help="live dashboard with auto-rescan")
    v.add_argument("--port", type=int, default=8787)
    v.add_argument("--no-open", action="store_true",
                   help="don't auto-open the browser")
    v.set_defaults(fn=_cmd_serve)

    sub.add_parser("open", help="open the dashboard in your browser").set_defaults(fn=_cmd_open)
    sub.add_parser("doctor", help="check setup; show fixes for anything missing").set_defaults(fn=_cmd_doctor)

    ib = sub.add_parser("inbox",
        help="print the canonical path for a new artifact (date-prefixed slug)")
    ib.add_argument("topic", nargs="*",
                    help="topic words → filename slug (defaults to 'untitled')")
    ib.set_defaults(fn=_cmd_inbox)

    isk = sub.add_parser("install-skill",
        help="install the /craft Claude Code skill into ~/.claude/skills/")
    isk.add_argument("--dest", help="install to a specific path "
                                     "(default: ~/.claude/skills/craft/)")
    isk.add_argument("--force", action="store_true", help="overwrite if present")
    isk.set_defaults(fn=_cmd_install_skill)

    dg = sub.add_parser("designs", help="list or dump design fingerprints (style + skeleton)")
    dg.add_argument("id", nargs="?", help="artifact id prefix (from `folio designs`)")
    dg_g = dg.add_mutually_exclusive_group()
    dg_g.add_argument("--template", action="store_true",
                      help="dump CSS + body skeleton (paste into Claude as style example)")
    dg_g.add_argument("--css", action="store_true",
                      help="dump just the <style> contents")
    dg_g.add_argument("--skeleton", action="store_true",
                      help="dump just the body skeleton (no text)")
    dg.set_defaults(fn=_cmd_designs)

    lk = sub.add_parser("link", help="attach source URL / tool / prompt to a file")
    lk.add_argument("file")
    lk.add_argument("--source", help="chat or artifact URL")
    lk.add_argument("--tool", choices=["claude", "chatgpt", "v0", "lovable",
                                         "bolt", "gemini", "cursor", "manual"],
                    help="generating tool")
    lk.add_argument("--model", help="model id (e.g. claude-opus-4-7)")
    lk.add_argument("--prompt", help="the prompt that produced it")
    lk.add_argument("--tag", action="append", default=[], help="add a tag (repeatable)")
    lk.add_argument("--note", help="free-form note")
    lk.set_defaults(fn=_cmd_link)

    inf = sub.add_parser("info", help="show provenance for a file")
    inf.add_argument("file"); inf.set_defaults(fn=_cmd_info)

    sh = sub.add_parser("share", help="publish an artifact to a public URL (GitHub Pages)")
    sh.add_argument("file", nargs="?", help="HTML file to share")
    sh.add_argument("--list", action="store_true", help="list previous shares")
    sh.add_argument("--revoke", metavar="ID", help="delete a previously-shared artifact")
    sh.add_argument("--no-clipboard", action="store_true",
                    help="don't copy the URL to clipboard")
    sh.set_defaults(fn=_cmd_share)

    im = sub.add_parser("import", help="fetch a shared AI-artifact URL into your library")
    im.add_argument("url")
    im.add_argument("--name", help="override filename (no .html needed)")
    im.add_argument("--drop-dir", help="save into this dir (defaults to ~/folio-inbox)")
    im.set_defaults(fn=_cmd_import)

    args = p.parse_args(argv)
    if not getattr(args, "fn", None):
        # default: serve (initial scan happens inside if no dashboard yet)
        return _cmd_serve(argparse.Namespace(port=8787, no_open=False))
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
