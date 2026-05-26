"""LLM-derived intent metadata for an artifact (opt-in extra).

This is the *only* part of Artifold that calls out to an LLM. It's gated by:
  1. `pip install artifold[intent]` (pulls the `anthropic` SDK)
  2. `ANTHROPIC_API_KEY` set in the environment
  3. `enable_intent: true` in config OR `artifold scan --intent` for one run

Default Artifold is fully local; this module is only loaded when explicitly used.

One Claude Haiku call per artifact, cached forever by content SHA1 in the
provenance store.

Output schema (all best-effort, all optional):
    {
      "intent":   "10-15 word description of what the artifact accomplishes",
      "topic":    ["1-4 short lowercase tags"],
      "audience": "self | <named person> | team | public | unknown",
      "voice":    "data-dense | warm-encouraging | technical-explainer |
                   playful | professional | instructional | minimalist | narrative",
    }
"""
from __future__ import annotations

import asyncio
import json
import os
import re

from . import config

DEFAULT_MODEL = "claude-haiku-4-5"

# Use prompt caching on the system prompt: it never changes across calls
# in one run, and Anthropic's ephemeral cache cuts cost ~90% on system tokens.
SYSTEM = """You analyze HTML artifacts a user has generated (often with an AI tool) \
and return a compact JSON metadata object summarizing them.

Return ONLY valid JSON. No preamble, no code fences, no commentary.

Schema:
{
  "intent":   "<10-15 word description of what this artifact accomplishes>",
  "topic":    ["<1-4 lowercase short tags, kebab-case if multi-word>"],
  "audience": "<who it's for: 'self', a named person if obvious, 'team', 'public', or 'unknown'>",
  "voice":    "<one of: data-dense | warm-encouraging | technical-explainer | playful | professional | instructional | minimalist | narrative>"
}

Examples of good intent lines:
- "Printable 30-day strength + cardio tracker, kettlebell focus"
- "12-week ML interview prep plan with weekly milestones"
- "Personal one-pager pitching a 4-day SoCal road trip"
- "Action-plan tracker for EB1A green card filing"

Keep intent under 18 words. Be specific. Do not invent details."""


def _strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


def have_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def enabled(cfg: dict | None = None) -> bool:
    cfg = cfg or config.load()
    return bool(cfg.get("enable_intent")) and have_api_key()


async def _infer_one(client, model: str, title: str, body_text: str) -> dict | None:
    try:
        msg = await client.messages.create(
            model=model,
            max_tokens=320,
            system=[{"type": "text", "text": SYSTEM,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{
                "role": "user",
                "content": (f"Artifact title: {title or '(none)'}\n\n"
                            f"Artifact text (first 4000 chars of visible body):\n"
                            f"{(body_text or '')[:4000]}"),
            }],
        )
        txt = _strip_fences(msg.content[0].text)
        data = json.loads(txt)
        # minimal sanity: must have 'intent'
        if not isinstance(data, dict) or not data.get("intent"):
            return None
        # normalize types
        if isinstance(data.get("topic"), str):
            data["topic"] = [data["topic"]]
        return {k: data[k] for k in ("intent", "topic", "audience", "voice")
                if k in data}
    except Exception as e:
        print(f"    ! intent inference failed: {type(e).__name__}: {e}")
        return None


async def infer_many(items: list[tuple[str, str, str]],     # (sha, title, body)
                     model: str = DEFAULT_MODEL,
                     concurrency: int = 5) -> dict[str, dict]:
    """Infer intent for many artifacts in parallel. Returns sha → metadata."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        print("  ! intent inference requires the [intent] extra.\n"
              "    install:  pip install 'artifold[intent]'")
        return {}

    if not have_api_key():
        print("  ! intent inference enabled but ANTHROPIC_API_KEY not set; skipping.")
        return {}

    client = AsyncAnthropic()
    sem = asyncio.Semaphore(concurrency)
    out: dict[str, dict] = {}

    async def one(sha, title, body):
        async with sem:
            r = await _infer_one(client, model, title, body)
            if r:
                out[sha] = r

    print(f"  inferring intent for {len(items)} artifact(s) via {model}…")
    await asyncio.gather(*(one(*it) for it in items))
    print(f"    got intent for {len(out)}/{len(items)}")
    return out


def infer_many_sync(items: list[tuple[str, str, str]],
                    model: str = DEFAULT_MODEL,
                    concurrency: int = 5) -> dict[str, dict]:
    return asyncio.run(infer_many(items, model=model, concurrency=concurrency))
