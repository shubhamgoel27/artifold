"""Version diff: what changed between two iterations of an artifact.

Renders a standalone HTML page: two live previews side by side, plus a
unified diff of the *visible text* (scripts/styles stripped, block tags
treated as line breaks). Diffing rendered text instead of raw HTML keeps
CSS churn out of the way and answers the actual question: "what did the
new version say that the old one didn't?"
"""
from __future__ import annotations

import difflib
import html as html_mod
import re
from datetime import datetime
from pathlib import Path

_SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
_BLOCK_RE = re.compile(
    r"</?(?:p|div|section|article|li|tr|table|h[1-6]|br|hr|blockquote|"
    r"header|footer|figure|figcaption|dt|dd|pre)\b[^>]*>", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_MAX_LINES = 4000


def text_lines(raw: str) -> list[str]:
    """Visible text of an HTML document as cleaned, non-empty lines."""
    raw = _SCRIPT_RE.sub(" ", raw)
    raw = _BLOCK_RE.sub("\n", raw)
    raw = _TAG_RE.sub(" ", raw)
    raw = html_mod.unescape(raw)
    lines = []
    for ln in raw.splitlines():
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            lines.append(ln)
        if len(lines) >= _MAX_LINES:
            break
    return lines


def _esc(s: str) -> str:
    return html_mod.escape(s, quote=True)


def _label(p: Path) -> str:
    try:
        ts = datetime.fromtimestamp(p.stat().st_mtime).strftime("%b %d, %Y %H:%M")
    except OSError:
        ts = ""
    return f"{p.name} · {ts}" if ts else p.name


def render_diff_page(old: Path, new: Path,
                     old_url: str, new_url: str) -> str:
    """Self-contained diff page. old/new are local files (for text + labels);
    old_url/new_url are the browser-reachable preview URLs (/file?p=…)."""
    old_lines = text_lines(old.read_text(encoding="utf-8", errors="ignore"))
    new_lines = text_lines(new.read_text(encoding="utf-8", errors="ignore"))
    rows = []
    added = removed = 0
    for ln in difflib.unified_diff(old_lines, new_lines,
                                   lineterm="", n=2):
        if ln.startswith("---") or ln.startswith("+++"):
            continue
        if ln.startswith("@@"):
            rows.append(f'<div class="hunk">{_esc(ln)}</div>')
        elif ln.startswith("+"):
            added += 1
            rows.append(f'<div class="add">{_esc(ln[1:])}</div>')
        elif ln.startswith("-"):
            removed += 1
            rows.append(f'<div class="del">{_esc(ln[1:])}</div>')
        else:
            rows.append(f'<div class="ctx">{_esc(ln[1:])}</div>')
    if not rows:
        rows = ['<div class="ctx" style="padding:14px">'
                'No visible-text changes. The versions differ only in '
                'markup, styling or scripts.</div>']
    summary = f"+{added} / −{removed} lines of visible text"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>diff · {_esc(new.name)}</title>
<style>
  :root {{ --bg:#0a0d12; --surface:#121620; --line:rgba(255,255,255,.08);
           --text:#e8ecf2; --mut:#8a93a6; --add:#1d3a2a; --del:#3a1d22;
           --addink:#7ee2a8; --delink:#f29ba6; }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg:#fafbfc; --surface:#fff; --line:rgba(15,23,42,.1);
             --text:#16181d; --mut:#5d6679; --add:#e6f4ea; --del:#fbe9eb;
             --addink:#0a6b35; --delink:#a01a2e; }} }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ background:var(--bg); color:var(--text);
         font:14px/1.5 -apple-system, BlinkMacSystemFont, Inter, sans-serif; }}
  header {{ display:flex; gap:12px; align-items:baseline; padding:12px 18px;
            border-bottom:1px solid var(--line); flex-wrap:wrap; }}
  header b {{ font-size:15px; }}
  header .sum {{ color:var(--mut); font-size:12.5px; }}
  .panes {{ display:grid; grid-template-columns:1fr 1fr; gap:1px;
            background:var(--line); height:52vh; }}
  .pane {{ background:var(--bg); display:flex; flex-direction:column; min-width:0; }}
  .pane .cap {{ padding:6px 12px; font-size:11.5px; color:var(--mut);
               background:var(--surface); border-bottom:1px solid var(--line);
               white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .pane .cap .tag {{ font-weight:600; margin-right:8px; }}
  .pane.old .cap .tag {{ color:var(--delink); }}
  .pane.new .cap .tag {{ color:var(--addink); }}
  .pane iframe {{ flex:1; border:0; width:100%; background:#fff; }}
  .diff {{ font:12px/1.6 ui-monospace, SFMono-Regular, Menlo, monospace;
           padding:10px 0 60px; }}
  .diff > div {{ padding:1px 18px; white-space:pre-wrap; word-break:break-word; }}
  .diff .add {{ background:var(--add); color:var(--addink); }}
  .diff .del {{ background:var(--del); color:var(--delink); }}
  .diff .ctx {{ color:var(--mut); }}
  .diff .hunk {{ color:var(--mut); opacity:.7; padding-top:10px; }}
  @media (max-width:760px) {{ .panes {{ grid-template-columns:1fr; height:auto; }}
    .pane iframe {{ height:40vh; }} }}
</style></head><body>
<header><b>Version diff</b><span class="sum">{_esc(summary)}</span></header>
<div class="panes">
  <div class="pane old"><div class="cap"><span class="tag">OLD</span>{_esc(_label(old))}</div>
    <iframe src="{_esc(old_url)}" title="old version"></iframe></div>
  <div class="pane new"><div class="cap"><span class="tag">NEW</span>{_esc(_label(new))}</div>
    <iframe src="{_esc(new_url)}" title="new version"></iframe></div>
</div>
<div class="diff">{''.join(rows)}</div>
</body></html>"""
