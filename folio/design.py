"""Extract a lightweight 'design fingerprint' from an HTML artifact — pure regex,
no LLM, no network.

The fingerprint captures the *reusable* design language of the artifact:
color palette, typography, design tokens (CSS variables), gradient/glass
signals, border-radius mood, and a hash of the DOM skeleton.

Use:
- `extract(html)` → JSON-able dict; cached per file by content SHA1
- `as_template(html)` → ready-to-paste material (CSS + content-free skeleton)
  for handing to an LLM as "make new report in this style"

The CSS + skeleton dump is the useful primitive — Folio extracts and serves
it; whichever LLM the user prefers does the actual generation.
"""
from __future__ import annotations

import re
from collections import Counter

STYLE_RE   = re.compile(r"<style[^>]*>(.*?)</style>", re.I | re.S)
SCRIPT_RE  = re.compile(r"<script[^>]*>.*?</script>", re.I | re.S)
COMMENT_RE = re.compile(r"<!--.*?-->|/\*.*?\*/", re.S)

HEX_RE      = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
FONT_RE     = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)
RADIUS_RE   = re.compile(r"border-radius\s*:\s*(\d+(?:\.\d+)?)\s*(px|rem|em)?", re.I)
GRADIENT_RE = re.compile(r"(linear|radial|conic)-gradient\b", re.I)
GLASS_RE    = re.compile(r"backdrop-filter\s*:\s*blur", re.I)
DARKMODE_RE = re.compile(r"\[data-theme\s*=\s*['\"]?(?:dark|light)|prefers-color-scheme", re.I)
ROOT_RE     = re.compile(r":root[^{]*\{([^}]+)\}", re.I)
VAR_DEF_RE  = re.compile(r"--([\w-]+)\s*:\s*([^;]+);?", re.I)
ANIM_RE     = re.compile(r"@keyframes|animation\s*:", re.I)
SHADOW_RE   = re.compile(r"box-shadow\s*:\s*([^;}]+)", re.I)


def _all_styles(html: str) -> str:
    return " ".join(STYLE_RE.findall(html))


def _palette(styles: str, max_n: int = 6) -> list[str]:
    """Most-frequent color values, normalized + deduped."""
    raw = [c.lower() for c in HEX_RE.findall(styles)]
    # collapse 3-digit hex (#abc → #aabbcc) so #fff and #ffffff dedup
    canon = []
    for h in raw:
        body = h[1:]
        if len(body) == 3:
            canon.append("#" + "".join(c * 2 for c in body))
        elif len(body) == 4:
            canon.append("#" + "".join(c * 2 for c in body))
        else:
            canon.append(h)
    counts = Counter(canon)
    return [c for c, _ in counts.most_common(max_n)]


def _fonts(styles: str, max_n: int = 4) -> list[str]:
    """Distinct font-family primaries (first family in each declaration)."""
    out: list[str] = []
    for m in FONT_RE.finditer(styles):
        # take the first family in the stack, strip quotes
        first = m.group(1).split(",")[0].strip().strip("'\"")
        if first and first not in out and not first.startswith("var("):
            out.append(first)
        if len(out) >= max_n:
            break
    return out


def _design_tokens(styles: str, max_n: int = 24) -> dict:
    """CSS custom properties from :root — the artifact's design system."""
    tokens: dict[str, str] = {}
    for root_block in ROOT_RE.finditer(styles):
        for m in VAR_DEF_RE.finditer(root_block.group(1)):
            tokens[m.group(1)] = m.group(2).strip()
    # Keep small subset to avoid bloat
    return dict(list(tokens.items())[:max_n])


def _density(html: str) -> int:
    """Rough text-density signal: visible body text length (after tag strip)."""
    body = re.sub(SCRIPT_RE, " ", html)
    body = re.sub(STYLE_RE, " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    return len(re.sub(r"\s+", " ", body).strip())


def _skeleton(html: str, max_chars: int = 6000) -> str:
    """Body markup with all text/scripts/styles stripped — preserves structure
    + class names so an LLM can see the layout vocabulary."""
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.I | re.S)
    body = m.group(1) if m else html
    body = SCRIPT_RE.sub("", body)
    body = STYLE_RE.sub("", body)
    body = COMMENT_RE.sub("", body)
    # collapse whitespace AND remove text nodes between tags
    body = re.sub(r">\s*[^<]+\s*<", "><", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:max_chars]


def extract(html: str) -> dict:
    """Compact design fingerprint suitable for storing per-artifact."""
    styles = _all_styles(html)
    radii = [float(m.group(1)) for m in RADIUS_RE.finditer(styles)]
    return {
        "palette":      _palette(styles),
        "fonts":        _fonts(styles),
        "tokens":       _design_tokens(styles),
        "gradient":     bool(GRADIENT_RE.search(styles)),
        "glass":        bool(GLASS_RE.search(styles)),
        "themed":       bool(DARKMODE_RE.search(styles)),
        "animated":     bool(ANIM_RE.search(styles)),
        "shadowed":     bool(SHADOW_RE.search(styles)),
        "avg_radius":   round(sum(radii) / len(radii), 1) if radii else 0,
        "density":      _density(html),
        "skeleton_len": len(_skeleton(html)),
        "css_len":      len(styles),
    }


def as_template(html: str, include_css: bool = True,
                include_skeleton: bool = True) -> str:
    """Ready-to-paste material: the artifact's CSS + a content-free skeleton
    of its body. Intended for `folio designs <id> --template` and direct
    paste into a Claude/ChatGPT/Cursor chat."""
    out = []
    if include_css:
        styles = STYLE_RE.findall(html)
        if styles:
            out.append("/* === styles === */")
            out.append("<style>")
            out.append("\n".join(s.strip() for s in styles))
            out.append("</style>")
    if include_skeleton:
        out.append("\n<!-- === body skeleton (text removed) === -->")
        out.append(_skeleton(html))
    return "\n".join(out)
