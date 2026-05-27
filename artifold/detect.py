"""Best-effort source detection from HTML content.

Conservative: only fires on explicit "built with" markers / URL references
so we don't false-positive somebody's own writing. Returns a tool slug
matching provenance.VALID_TOOLS or None.
"""
from __future__ import annotations

import re

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("v0",       re.compile(r"\b(?:v0\.dev|data-v0|built with v0)\b", re.I)),
    ("lovable",  re.compile(r"\b(?:lovable\.dev|built with lovable|gptengineer)\b", re.I)),
    ("bolt",     re.compile(r"\b(?:bolt\.new|powered by bolt|stackblitz/bolt)\b", re.I)),
    ("chatgpt",  re.compile(r"chatgpt\.com/(?:canvas|c)/|openai canvas", re.I)),
    ("claude",   re.compile(r"claude\.ai/(?:artifacts|chat|share)/|claude artifact",
                            re.I)),
    ("gemini",   re.compile(r"gemini\.google\.com|gemini canvas", re.I)),
    ("cursor",   re.compile(r"\b(?:cursor\.sh|cursor ide)\b", re.I)),
]

# Explicit artifold:* meta tags emitted by our /craft skill (and any tool
# that wants to pre-populate provenance). Legacy folio:* names supported.
def _meta(tag: str) -> re.Pattern:
    return re.compile(
        rf'<meta\s+name=["\'](?:artifold|folio):{tag}["\']\s+content=["\']([^"\']+)["\']',
        re.I)

META_INTENT         = _meta("intent")
META_TOOL           = _meta("tool")
META_MODEL          = _meta("model")
META_SOURCE         = _meta("source")
META_PROMPT         = _meta("prompt")
META_DESIGN_MODE    = _meta("design-mode")
META_VOICE_REGISTER = _meta("voice-register")
META_STYLE_FROM     = _meta("style-from")


def detect_tool(html: str) -> str | None:
    head = html[:80000]   # check generous head; markers may be in footer too
    for tool, pat in PATTERNS:
        if pat.search(head):
            return tool
    return None


def extract_embedded_meta(html: str) -> dict:
    """Pull artifold:* meta tags (emitted by our own generator) for zero-LLM provenance.
    Map the dashed tag names to underscored Python-friendly keys."""
    head = html[:8000]   # meta tags are in <head>
    out: dict = {}
    fields = [
        ("intent",         META_INTENT),
        ("tool",           META_TOOL),
        ("model",          META_MODEL),
        ("source",         META_SOURCE),
        ("prompt",         META_PROMPT),
        ("design_mode",    META_DESIGN_MODE),
        ("voice_register", META_VOICE_REGISTER),
        ("style_from",     META_STYLE_FROM),
    ]
    for key, pat in fields:
        m = pat.search(head)
        if m:
            out[key] = m.group(1)
    return out
