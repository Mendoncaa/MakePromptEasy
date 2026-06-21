"""File filtering logic for prompt-pack."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from prompt_pack.config import (
    DEFAULT_IGNORE_DIRS,
    DEFAULT_IGNORE_EXTENSIONS,
    DEFAULT_IGNORE_FILENAMES,
    MAX_FILE_SIZE_BYTES,
    SENSITIVE_PATTERNS,
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


def _is_sensitive_name(path: Path) -> bool:
    """Return True if *path*'s name is a known secret/credential file.

    Checks exact filenames (``.env``, ``id_rsa``…) and glob patterns
    (``.env.*``, ``*.pem``, ``id_rsa*``…). Name-only — no I/O.
    """
    if path.name in DEFAULT_IGNORE_FILENAMES:
        return True
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in SENSITIVE_PATTERNS)


def is_sensitive(path: Path) -> bool:
    """Return True if *path* is a secret/credential or binary file.

    Applied in *every* scan mode — including ``--extensions`` allow-list
    mode — so that secrets (``.env``, ``*.pem``, ``id_rsa``…) and binary
    blobs are never packed regardless of the chosen extension filter.
    """
    if _is_sensitive_name(path):
        return True
    return path.is_file() and _is_binary(path)


def should_ignore(path: Path, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> bool:
    """Return True if *path* should be excluded from the prompt pack.

    Checks (in order, cheapest first):
    1. Filename exact match / sensitive filename glob pattern
    2. Extension match
    3. Directory name match
    4. File size exceeds *max_size_bytes*
    5. Binary content sniff
    """
    if _is_sensitive_name(path):
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

    # Sniff for binary content (null bytes in first 8 KB) — files only
    if path.is_file():
        return _is_binary(path)

    return False


_BINARY_SNIFF_SIZE = 8192


def _is_binary(path: Path) -> bool:
    """Return True if *path* appears to be a binary file.

    Reads only the first 8 KB and checks for null bytes — a reliable
    heuristic used by Git itself. Streaming the read avoids loading large
    files fully into memory just to inspect their header.
    """
    try:
        with path.open("rb") as fh:
            chunk = fh.read(_BINARY_SNIFF_SIZE)
    except OSError:
        return True  # Can't read → treat as binary
    return b"\x00" in chunk
