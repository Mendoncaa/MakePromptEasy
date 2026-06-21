"""Markdown formatter for prompt-pack."""

from __future__ import annotations

import datetime
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# Map of file extension → Markdown fenced-code language hint
_LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".mdx": "markdown",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "fish",
    ".ps1": "powershell",
    ".rb": "ruby",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".r": "r",
    ".sql": "sql",
    ".lua": "lua",
    ".vim": "vim",
    ".dockerfile": "dockerfile",
    ".tf": "hcl",
    ".hcl": "hcl",
    ".xml": "xml",
    ".ini": "ini",
    ".cfg": "ini",
    ".env": "bash",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".proto": "protobuf",
    ".dart": "dart",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".clj": "clojure",
    ".scala": "scala",
}


def _language_hint(path: Path) -> str:
    """Return the Markdown code-fence language tag for *path*."""
    name_lower = path.name.lower()
    # Handle files like 'Dockerfile' with no extension
    if name_lower in {"dockerfile", "makefile", "cmakelists.txt"}:
        return "dockerfile" if "dockerfile" in name_lower else "makefile"
    return _LANG_MAP.get(path.suffix.lower(), "")


def estimate_tokens(text: str | int) -> int:
    """Rough token estimate: 1 token ≈ 4 characters (GPT-4 rule of thumb)."""
    chars = len(text) if isinstance(text, str) else text
    return max(1, chars // 4)


def _slugify(posix_path: str) -> str:
    """Convert a POSIX path string to a GitHub-compatible anchor slug.

    GitHub's anchor algorithm: lowercase, strip non-alphanumeric except
    spaces and hyphens, then convert spaces to hyphens, collapse runs.

    Since our paths have slashes, dots, and underscores, we convert them
    all to hyphens first, which produces readable slugs like
    ``src-utils-v2-py`` from ``src/utils_v2.py``.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", posix_path.lower())
    return slug.strip("-")


def _compute_fence(content: str) -> str:
    """Return a backtick fence longer than any backtick run in *content*.

    CommonMark allows fences with N≥3 backticks.  We scan the content for
    the longest consecutive run of backticks and use max(3, longest+1).
    """
    longest = 0
    for match in re.finditer(r"`+", content):
        longest = max(longest, len(match.group()))
    n = max(3, longest + 1)
    return "`" * n


@dataclass(frozen=True, slots=True)
class PackResult:
    """Result of packing files — contains the markdown and consistent metrics."""

    markdown: str
    file_count: int
    total_lines: int
    total_chars: int
    estimated_tokens: int


def build_markdown(files: Iterable[Path], root: Path) -> PackResult:
    """Build the complete Markdown string from a collection of file paths.

    Args:
        files: Iterable of absolute Path objects to include.
        root: The root directory used as base for relative path display.

    Returns:
        A Markdown string ready to be written to disk or copied to clipboard.
    """
    file_list = list(files)  # materialise once — we need len + two passes

    # ── Collect file contents ────────────────────────────────────────────────
    sections: list[str] = []
    total_lines = 0
    total_chars = 0
    skipped: set[Path] = set()

    for path in file_list:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            skipped.add(path)
            continue

        rel = path.relative_to(root) if path.is_relative_to(root) else path
        lang = _language_hint(path)
        total_lines += content.count("\n") + 1
        total_chars += len(content)

        fence = _compute_fence(content)
        anchor = _slugify(rel.as_posix())
        section = (
            f'<a id="{anchor}"></a>\n\n'
            f"### `{rel.as_posix()}`\n\n{fence}{lang}\n{content}\n{fence}"
        )
        sections.append(section)

    # ── Header ───────────────────────────────────────────────────────────────
    now = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    header_lines = [
        "# Prompt Pack",
        "",
        f"> **Source:** `{root.as_posix()}`  ",
        f"> **Generated:** {now}  ",
        f"> **Files:** {len(sections)}  ",
        f"> **Lines:** {total_lines:,}  ",
        f"> **Estimated tokens:** ~{estimate_tokens(total_chars):,}  ",
        "",
        "---",
        "",
    ]

    if skipped:
        skipped_note = (
            "> ⚠️ **Skipped (unreadable):** "
            + ", ".join(f"`{p.name}`" for p in sorted(skipped, key=lambda p: p.name))
            + "\n\n---\n"
        )
        header_lines.append(skipped_note)

    # ── Table of contents ────────────────────────────────────────────────────
    toc_lines = ["## Table of Contents", ""]
    for path in file_list:
        if path in skipped:
            continue
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        anchor = _slugify(rel.as_posix())
        toc_lines.append(f"- [`{rel.as_posix()}`](#{anchor})")
    toc_lines += ["", "---", ""]

    # ── Body ─────────────────────────────────────────────────────────────────
    body = "\n\n".join(sections)

    # ── Footer ───────────────────────────────────────────────────────────────
    footer = (
        "\n\n---\n\n"
        f"*Generated by [prompt-pack](https://github.com/Mendoncaa/MakePromptEasy) · "
        f"{len(sections)} file(s) · {total_lines:,} line(s)"
        f" · ~{estimate_tokens(total_chars):,} tokens*\n"
    )

    return PackResult(
        markdown="\n".join(header_lines) + "\n".join(toc_lines) + body + footer,
        file_count=len(sections),
        total_lines=total_lines,
        total_chars=total_chars,
        estimated_tokens=estimate_tokens(total_chars),
    )
