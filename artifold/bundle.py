"""Inline local sibling assets into a single self-contained HTML file.

Used at share time so multi-file projects (HTML + sibling CSS/JS/images)
become one portable artifact that can be uploaded to GitHub Pages as a
single .html file.

Conservative scope:
  - `<link rel="stylesheet" href="local.css">` → <style>…</style>
  - `<script src="local.js">…</script>` → <script>…</script> (src dropped)
  - `<img src="local.png">` → data: URI (if under MAX_INLINE_BYTES)
  - `url(local.foo)` inside inlined CSS → data: URI (same cap)

Remote URLs (http://, https://, //, data:) are left alone. Anything that
can't be resolved on disk is left alone with a warning.
"""
from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

# Per-asset cap. Above this, leave the reference alone — inlining huge images
# bloats the share file and slows page load on the receiving end.
MAX_INLINE_BYTES = 500 * 1024

# Asset types we'll inline. Images get data: URIs; text gets inlined as text.
TEXT_EXTS  = {".css", ".js", ".mjs", ".json", ".svg", ".txt"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}
FONT_EXTS  = {".woff", ".woff2", ".ttf", ".otf"}

_LINK_RE   = re.compile(
    r'<link\s+([^>]*?)rel\s*=\s*["\']?stylesheet["\']?([^>]*?)\s*/?>',
    re.I | re.S)
_SCRIPT_RE = re.compile(
    r'<script\b([^>]*?)\bsrc\s*=\s*["\']([^"\']+)["\']([^>]*?)\s*(/>|>\s*</script\s*>)',
    re.I | re.S)
_IMG_RE    = re.compile(
    r'<img\s+([^>]*?)src\s*=\s*["\']([^"\']+)["\']([^>]*?)/?>',
    re.I | re.S)
_HREF_ATTR = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)
_URL_RE    = re.compile(r'url\(\s*(["\']?)([^"\')]+)\1\s*\)', re.I)


def _is_remote(url: str) -> bool:
    u = url.strip().lower()
    return (u.startswith("http://") or u.startswith("https://")
            or u.startswith("//") or u.startswith("data:")
            or u.startswith("mailto:") or u.startswith("tel:")
            or u.startswith("javascript:") or u.startswith("#"))


def _resolve(base_dir: Path, ref: str) -> Path | None:
    """Resolve a relative URL against base_dir. Returns None if outside dir
    (path traversal) or doesn't exist."""
    # Strip query / fragment
    ref = ref.split("?", 1)[0].split("#", 1)[0]
    if not ref:
        return None
    try:
        p = (base_dir / ref).resolve()
        # Must stay under base_dir
        p.relative_to(base_dir.resolve())
    except (ValueError, OSError):
        return None
    if not p.is_file():
        return None
    return p


def _data_uri(path: Path) -> str | None:
    """base64 data: URI for binary assets. Returns None if file too big."""
    size = path.stat().st_size
    if size > MAX_INLINE_BYTES:
        return None
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        ext = path.suffix.lower()
        if ext == ".woff2": mime = "font/woff2"
        elif ext == ".woff": mime = "font/woff"
        elif ext == ".ttf":  mime = "font/ttf"
        elif ext == ".otf":  mime = "font/otf"
        else: mime = "application/octet-stream"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _inline_css_urls(css_text: str, base_dir: Path) -> str:
    """Rewrite url(…) refs inside CSS to data: URIs where possible."""
    def repl(m: re.Match) -> str:
        quote, ref = m.group(1), m.group(2)
        if _is_remote(ref):
            return m.group(0)
        p = _resolve(base_dir, ref)
        if not p:
            return m.group(0)  # leave broken refs alone (visible miss is honest)
        ext = p.suffix.lower()
        if ext in IMAGE_EXTS or ext in FONT_EXTS:
            data = _data_uri(p)
            if data:
                return f"url({quote}{data}{quote})"
        return m.group(0)
    return _URL_RE.sub(repl, css_text)


def _bundle_link(m: re.Match, base_dir: Path, warnings: list[str]) -> str:
    """Replace a <link rel=stylesheet> with an inlined <style> block, if local."""
    attrs = m.group(1) + " " + m.group(2)
    href_m = _HREF_ATTR.search(attrs)
    if not href_m:
        return m.group(0)
    href = href_m.group(1)
    if _is_remote(href):
        return m.group(0)
    p = _resolve(base_dir, href)
    if not p:
        warnings.append(f"missing stylesheet: {href}")
        return m.group(0)
    try:
        css = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        warnings.append(f"could not read {href}: {e}")
        return m.group(0)
    css = _inline_css_urls(css, p.parent)  # resolve url(…) relative to CSS file's dir
    # If the original <link> had a `media=` attr, preserve it.
    media_m = re.search(r'media\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
    media_attr = f' media="{media_m.group(1)}"' if media_m else ""
    return f"<style{media_attr} data-inlined-from=\"{href}\">\n{css}\n</style>"


def _bundle_script(m: re.Match, base_dir: Path, warnings: list[str]) -> str:
    pre_attrs, src, post_attrs, _close = m.group(1), m.group(2), m.group(3), m.group(4)
    if _is_remote(src):
        return m.group(0)
    p = _resolve(base_dir, src)
    if not p:
        warnings.append(f"missing script: {src}")
        return m.group(0)
    try:
        js = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        warnings.append(f"could not read {src}: {e}")
        return m.group(0)
    # Preserve type/defer/async if present — they still matter for parsing semantics.
    keep = []
    for attr in ("type", "defer", "async", "nomodule"):
        am = re.search(rf'\b{attr}(?:\s*=\s*["\']([^"\']*)["\'])?', pre_attrs + post_attrs, re.I)
        if am:
            keep.append(am.group(0))
    attr_str = (" " + " ".join(keep)) if keep else ""
    # Escape any </script> in the JS body to prevent premature termination.
    js_safe = js.replace("</script", "<\\/script")
    return f"<script{attr_str} data-inlined-from=\"{src}\">\n{js_safe}\n</script>"


def _bundle_img(m: re.Match, base_dir: Path, warnings: list[str]) -> str:
    pre_attrs, src, post_attrs = m.group(1), m.group(2), m.group(3)
    if _is_remote(src):
        return m.group(0)
    p = _resolve(base_dir, src)
    if not p:
        return m.group(0)
    ext = p.suffix.lower()
    if ext not in IMAGE_EXTS:
        return m.group(0)
    data = _data_uri(p)
    if not data:
        warnings.append(f"img too large to inline: {src} ({p.stat().st_size} bytes > {MAX_INLINE_BYTES})")
        return m.group(0)
    return f'<img {pre_attrs}src="{data}"{post_attrs}>'


def bundle_html(path: Path) -> tuple[bytes, list[str]]:
    """Inline all local sibling assets referenced by `path`.

    Returns (bundled_bytes, warnings). The HTML's text encoding is preserved
    (we read+write as UTF-8 even when the source uses a different declared
    charset — modern browsers all handle utf-8 robustly).
    """
    base_dir = path.parent.resolve()
    html = path.read_text(encoding="utf-8", errors="ignore")
    warnings: list[str] = []

    html = _LINK_RE.sub(lambda m: _bundle_link(m, base_dir, warnings), html)
    html = _SCRIPT_RE.sub(lambda m: _bundle_script(m, base_dir, warnings), html)
    html = _IMG_RE.sub(lambda m: _bundle_img(m, base_dir, warnings), html)

    return html.encode("utf-8"), warnings


def has_local_refs(path: Path) -> bool:
    """Quick check: does this HTML reference any local sibling files?
    Used to decide whether bundling is worth running."""
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:32768]
    except Exception:
        return False
    base_dir = path.parent.resolve()
    for pat in (_LINK_RE, _SCRIPT_RE, _IMG_RE):
        for m in pat.finditer(head):
            attrs = " ".join(g for g in m.groups() if isinstance(g, str))
            for href_m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', attrs, re.I):
                ref = href_m.group(1)
                if _is_remote(ref):
                    continue
                if _resolve(base_dir, ref):
                    return True
    return False
