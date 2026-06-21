"""User-defined ignore patterns loaded from a .promptpackignore file."""

from __future__ import annotations

import fnmatch
from pathlib import Path

IGNORE_FILE_NAME = ".promptpackignore"


def load_ignore_patterns(root: Path) -> list[str]:
    """Read glob patterns from *root*/.promptpackignore.

    Rules:
    - Lines starting with ``#`` are comments and are ignored.
    - Blank lines are ignored.
    - All other lines are treated as Unix shell-style glob patterns
      (via :func:`fnmatch.fnmatch`).

    Returns an empty list if the file does not exist or cannot be read.
    """
    ignore_file = root / IGNORE_FILE_NAME
    if not ignore_file.exists():
        return []
    try:
        text = ignore_file.read_text(encoding="utf-8")
    except OSError:
        return []

    patterns: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns


def matches_ignore_pattern(
    path: Path,
    root: Path,
    patterns: list[str],
) -> bool:
    """Return True if *path* matches any pattern in *patterns*.

    Each pattern is tested against:

    1. The file/directory **name** only — so ``*.log`` matches ``app.log``
       anywhere in the tree.
    2. The **relative path** from *root* — so ``tests/*.log`` matches only
       ``tests/app.log``.

    Args:
        path: Absolute path to test.
        root: Root directory used to compute relative paths.
        patterns: Patterns loaded via :func:`load_ignore_patterns`.

    Returns:
        ``True`` if the path should be excluded, ``False`` otherwise.
    """
    if not patterns:
        return False

    try:
        rel = path.relative_to(root)
    except ValueError:
        return False

    rel_posix = rel.as_posix()
    name = path.name

    for pattern in patterns:
        # Strip trailing slash — it only signals "directory", handled by
        # matching the name/path regardless (scanner prunes entire dirs)
        pat = pattern.rstrip("/")
        if fnmatch.fnmatch(name, pat):
            return True
        if fnmatch.fnmatch(rel_posix, pat):
            return True

    return False
