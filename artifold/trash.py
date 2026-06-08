"""Move artifacts to the system Trash (recoverable), not hard-delete.

Why Trash, not unlink:
  - one misclick should not destroy a report you spent an hour generating
  - macOS Trash, Linux Trash, Windows Recycle Bin all support "Put Back"
  - artifold's provenance is hash-keyed, so if you restore the file from
    Trash it auto-reattaches to its old metadata on the next scan

Multi-file artifact note:
  This trashes only the HTML file passed in. Sibling CSS/JS/images stay
  on disk (orphaned but harmless). For total cleanup of a multi-file
  project, the user can drag the whole dir to Trash manually.
"""
from __future__ import annotations

from pathlib import Path


def trash_file(path: Path) -> tuple[bool, str]:
    """Move `path` to the system Trash. Returns (ok, message_or_error).

    Validates the path exists and is a file (won't trash directories
    through this function — too easy to wipe an entire project dir by
    mistake; if needed, do that explicitly through the OS).
    """
    path = path.expanduser().resolve()
    if not path.exists():
        return False, f"not found: {path}"
    if not path.is_file():
        return False, f"refusing to trash non-file (dir?): {path}"
    try:
        from send2trash import send2trash
    except ImportError:
        return False, ("send2trash not installed — pip install send2trash "
                       "(or upgrade artifold to 0.6.1+)")
    try:
        send2trash(str(path))
    except Exception as e:
        return False, f"trash failed: {type(e).__name__}: {e}"
    return True, str(path)
