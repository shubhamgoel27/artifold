"""Read provenance left behind by *other* design skills.

Artifold's own tags (`detect.extract_embedded_meta`) are the best case: a
skill states what it made and why. Most skills state nothing. Of the three
largest design skills on GitHub, only one writes anything into its output:

    taste-skill    83.3k stars   no marker, no memory
    hallmark       27.7k stars   CSS stamp + .hallmark/log.json
    huashu-design  23.8k stars   no marker, no memory

So this module is small on purpose. Where a skill leaves a durable record,
read it. Where it does not, `design.extract` still recovers the palette,
fonts, tokens and skeleton from the HTML itself, and the optional LLM
intent pass can fill the rest.

Every adapter fails soft. These are other people's formats and they move
without warning; a stamp that no longer parses yields no metadata, never
an exception. The raw foreign values are kept under `generator_native` so
a lossy mapping never destroys the original.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Hallmark stamps the first non-empty line of its CSS. Documented form:
#   /* Hallmark · macrostructure: <name> · tone: <tone> · anchor hue: <hue> */
# Real stamps run to several lines and carry extra keys (nav, footer, fonts,
# OKLCH values), so parse it as a `key: value` bag between `·` separators
# rather than pinning the field order.
HALLMARK_BLOCK_RE = re.compile(r"/\*\s*Hallmark\s*·(.+?)\*/", re.S | re.I)
HALLMARK_PAIR_RE = re.compile(r"([A-Za-z][\w \-]*?)\s*:\s*([^·\n]+)")

# How another skill's vocabulary lands in Artifold's fields. Lossy by
# nature: a macrostructure is not quite a layout archetype and a theme is
# not quite a design mode. Close enough to rotate against, which is the job.
HALLMARK_FIELD_MAP = {
    "macrostructure": "layout_archetype",
    "theme": "design_mode",
    "tone": "voice_register",
    "component": "signature_device",
}

LOG_REL = Path(".hallmark") / "log.json"
MAX_LOG_HOPS = 6          # how far up to look for a project root


def _clean(v: str) -> str:
    return re.sub(r"\s+", " ", v).strip().strip("·").strip()


def _hallmark_stamp(html: str) -> dict:
    """Parse Hallmark's CSS stamp out of an artifact."""
    m = HALLMARK_BLOCK_RE.search(html)
    if not m:
        return {}
    pairs = {}
    for k, v in HALLMARK_PAIR_RE.findall(m.group(1)):
        k = _clean(k).lower()
        v = _clean(v)
        if k and v:
            pairs.setdefault(k, v)
    return pairs


def _hallmark_log_entry(path: Path) -> dict:
    """Find the `.hallmark/log.json` entry for this artifact, if any.

    The log lives at the project root, so walk up looking for it. Entries
    are newest-first and carry a one-line `brief` — the closest thing
    Hallmark records to an intent.
    """
    try:
        here = path.resolve().parent
    except OSError:
        return {}
    for _ in range(MAX_LOG_HOPS):
        f = here / LOG_REL
        if f.is_file():
            try:
                entries = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                return {}
            if isinstance(entries, list) and entries:
                first = entries[0]
                return first if isinstance(first, dict) else {}
            return {}
        if here.parent == here:
            break
        here = here.parent
    return {}


def hallmark(html: str, path: Path) -> dict | None:
    """Provenance for an artifact built by Nutlope/hallmark."""
    stamp = _hallmark_stamp(html)
    if not stamp:
        return None                     # the stamp is the only proof
    log = _hallmark_log_entry(path)

    native = {**stamp}
    if log:
        native.update({f"log.{k}": v for k, v in log.items()
                       if isinstance(v, (str, int, float))})

    out: dict = {"generator": "hallmark", "generator_native": native}
    for foreign, ours in HALLMARK_FIELD_MAP.items():
        val = stamp.get(foreign) or log.get(foreign)
        if val:
            out[ours] = str(val)
    # `brief` is a one-line summary of what was asked for. That is an intent.
    brief = log.get("brief")
    if brief:
        out["intent"] = str(brief)
    return out


# Registry. Order matters only if two adapters could match one file, which
# no two currently can — each keys off a marker unique to its own tool.
ADAPTERS = [("hallmark", hallmark)]


def extract(html: str, path: Path) -> dict:
    """Try every adapter; return the first that recognises the artifact.

    Returns {} when nothing matches, which is the common case and not a
    failure — `design.extract` still fingerprints the file.
    """
    for _name, fn in ADAPTERS:
        try:
            got = fn(html, path)
        except Exception:
            continue                    # other people's formats; never fatal
        if got:
            return got
    return {}


def known_generators() -> list[str]:
    return [name for name, _ in ADAPTERS]
