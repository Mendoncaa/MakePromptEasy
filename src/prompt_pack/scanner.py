"""Recursive directory scanner for prompt-pack."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from prompt_pack.config import MAX_FILE_SIZE_BYTES
from prompt_pack.filters import should_ignore


def scan_directory(
    root: Path,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
) -> Generator[Path, None, None]:
    """Yield every non-ignored file under *root*, recursively.

    Uses a generator so large trees are traversed lazily — no up-front
    list allocation.  Directories that match ignore rules are pruned
    entirely (their contents are never visited).

    Args:
        root: The directory to scan.
        max_size_bytes: Per-file size cap; files above this are skipped.

    Yields:
        Absolute Path objects for each included file, sorted for
        deterministic output.

    Raises:
        NotADirectoryError: If *root* is not a directory.
        FileNotFoundError: If *root* does not exist.
    """
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    yield from _walk(root, max_size_bytes)


def _walk(directory: Path, max_size_bytes: int) -> Generator[Path, None, None]:
    """Internal recursive walk — sorted for determinism."""
    try:
        entries = sorted(
            directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
        )
    except PermissionError:
        return  # Skip directories we can't read

    for entry in entries:
        if entry.is_symlink():
            continue  # Never follow symlinks — avoids infinite loops

        if entry.is_dir():
            # Prune ignored directories entirely — don't descend into them
            if should_ignore(entry, max_size_bytes):
                continue
            yield from _walk(entry, max_size_bytes)

        elif entry.is_file():
            if not should_ignore(entry, max_size_bytes):
                yield entry
