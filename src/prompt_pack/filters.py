"""File filtering logic for prompt-pack."""

from __future__ import annotations

from pathlib import Path

from prompt_pack.config import (
    DEFAULT_IGNORE_DIRS,
    DEFAULT_IGNORE_EXTENSIONS,
    DEFAULT_IGNORE_FILENAMES,
    MAX_FILE_SIZE_BYTES,
)


def is_ignored_dir(path: Path) -> bool:
    """Return True if *path*'s own name matches an ignored directory pattern.

    Only the entry name is checked — not ancestor components — to avoid
    false positives when the absolute path to the project happens to
    contain an ignored name (e.g. a project at ``/home/user/env/project``
    must not be excluded because ``env`` appears in the path).

    The recursive walk in :func:`scan_directory` prunes entire directory
    subtrees, so any file that reaches :func:`should_ignore` is guaranteed
    not to live inside a previously-pruned directory.
    """
    name = path.name
    if name in DEFAULT_IGNORE_DIRS:
        return True
    # Match glob-style patterns like *.egg-info (only the name, not the full path)
    for pattern in DEFAULT_IGNORE_DIRS:
        if "*" in pattern and Path(name).match(pattern):
            return True
    return False


def should_ignore(path: Path, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> bool:
    """Return True if *path* should be excluded from the prompt pack.

    Checks (in order, cheapest first):
    1. Filename exact match
    2. Extension match
    3. Any ancestor directory match
    4. File size exceeds *max_size_bytes*
    """
    if path.name in DEFAULT_IGNORE_FILENAMES:
        return True

    if path.suffix.lower() in DEFAULT_IGNORE_EXTENSIONS:
        return True

    if is_ignored_dir(path):
        return True

    try:
        if path.stat().st_size > max_size_bytes:
            return True
    except OSError:
        # If we can't stat, skip the file to be safe
        return True

    return False
