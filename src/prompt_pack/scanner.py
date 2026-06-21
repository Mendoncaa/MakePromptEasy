"""Recursive directory scanner for prompt-pack."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from prompt_pack.config import MAX_FILE_SIZE_BYTES
from prompt_pack.filters import should_ignore
from prompt_pack.ignorefilter import load_ignore_patterns, matches_ignore_pattern


def scan_directory(
    root: Path,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
    ignore_patterns: list[str] | None = None,
    include_extensions: set[str] | None = None,
) -> Generator[Path, None, None]:
    """Yield every non-ignored file under *root*, recursively.

    Uses a generator so large trees are traversed lazily — no up-front
    list allocation.  Directories that match ignore rules are pruned
    entirely (their contents are never visited).

    Args:
        root: The directory to scan.
        max_size_bytes: Per-file size cap; files above this are skipped.
        ignore_patterns: Glob patterns to exclude. When ``None``, patterns
            are loaded automatically from *root*/.promptpackignore.
        include_extensions: When set, only files whose extension (lowercase,
            with leading dot) is in this set are yielded.  All other
            extension-based filtering is bypassed for these files.
            Example: ``{'.py', '.ts'}``.

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

    if ignore_patterns is None:
        ignore_patterns = load_ignore_patterns(root)

    yield from _walk(root, max_size_bytes, ignore_patterns, root, include_extensions)


def _walk(
    directory: Path,
    max_size_bytes: int,
    ignore_patterns: list[str],
    root: Path,
    include_extensions: set[str] | None = None,
) -> Generator[Path, None, None]:
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
            if matches_ignore_pattern(entry, root, ignore_patterns):
                continue
            yield from _walk(
                entry, max_size_bytes, ignore_patterns, root, include_extensions
            )

        elif entry.is_file():
            if include_extensions is not None:
                # Allow-list mode: only yield files with a matching extension
                if entry.suffix.lower() not in include_extensions:
                    continue
                # Still enforce size and user ignore patterns
                try:
                    if entry.stat().st_size > max_size_bytes:
                        continue
                except OSError:
                    continue
                if matches_ignore_pattern(entry, root, ignore_patterns):
                    continue
            else:
                if should_ignore(entry, max_size_bytes):
                    continue
                if matches_ignore_pattern(entry, root, ignore_patterns):
                    continue
            yield entry
