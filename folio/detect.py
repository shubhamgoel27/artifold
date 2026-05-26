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

# Also pick up explicit folio:* meta tags emitted by our own generator
META_INTENT = re.compile(r'<meta\s+name=["\']folio:intent["\']\s+content=["\']([^"\']+)["\']', re.I)
META_TOOL   = re.compile(r'<meta\s+name=["\']folio:tool["\']\s+content=["\']([^"\']+)["\']', re.I)
META_MODEL  = re.compile(r'<meta\s+name=["\']folio:model["\']\s+content=["\']([^"\']+)["\']', re.I)
META_SOURCE = re.compile(r'<meta\s+name=["\']folio:source["\']\s+content=["\']([^"\']+)["\']', re.I)
META_PROMPT = re.compile(r'<meta\s+name=["\']folio:prompt["\']\s+content=["\']([^"\']+)["\']', re.I)


def detect_tool(html: str) -> str | None:
    head = html[:80000]   # check generous head; markers may be in footer too
    for tool, pat in PATTERNS:
        if pat.search(head):
            return tool
    return None


def extract_embedded_meta(html: str) -> dict:
    """Pull folio:* meta tags (emitted by our own generator) for zero-LLM provenance."""
    head = html[:8000]   # meta tags are in <head>
    out: dict = {}
    for key, pat in [("intent", META_INTENT), ("tool", META_TOOL),
                     ("model", META_MODEL), ("source", META_SOURCE),
                     ("prompt", META_PROMPT)]:
        m = pat.search(head)
        if m:
            out[key] = m.group(1)
    return out
