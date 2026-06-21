"""CLI entry point for prompt-pack."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from prompt_pack import __version__
from prompt_pack.config import MAX_FILE_SIZE_BYTES
from prompt_pack.formatter import build_markdown
from prompt_pack.scanner import scan_directory

app = typer.Typer(
    name="prompt-pack",
    help="Pack a directory of code into a single Markdown prompt file.",
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)

_VERSION_CALLBACK_CALLED = False


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"prompt-pack {__version__}")
        raise typer.Exit()


@app.command()
def main(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to pack.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path. Defaults to 'prompt_output.md'.",
            writable=True,
            resolve_path=True,
        ),
    ] = None,
    no_clipboard: Annotated[
        bool,
        typer.Option("--no-clipboard", help="Skip copying to clipboard."),
    ] = False,
    stdout: Annotated[
        bool,
        typer.Option(
            "--stdout",
            help="Print output to stdout. No file is written; no summary panel.",
        ),
    ] = False,
    extensions: Annotated[
        str | None,
        typer.Option(
            "--extensions",
            "-e",
            help=(
                "Comma-separated file extensions to include (e.g. py,ts,go). "
                "Overrides default extension filtering — only these types are packed."
            ),
        ),
    ] = None,
    max_size: Annotated[
        int,
        typer.Option(
            "--max-size",
            help="Maximum file size to include, in KB.",
            min=1,
        ),
    ] = MAX_FILE_SIZE_BYTES // 1024,
    use_gitignore: Annotated[
        bool,
        typer.Option(
            "--use-gitignore",
            help="Also respect .gitignore rules when scanning.",
        ),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Pack *PATH* into a single Markdown file and copy it to the clipboard."""
    max_size_bytes = max_size * 1024

    # ── Mutual-exclusion guard ────────────────────────────────────────────────
    if stdout and output:
        err_console.print(
            "[yellow]Warning:[/] --output is ignored when --stdout is used."
        )

    # ── Parse --extensions ────────────────────────────────────────────────────
    include_extensions: set[str] | None = None
    if extensions:
        include_extensions = {
            f".{ext.lstrip('.')}" for ext in extensions.split(",") if ext.strip()
        }
        if not include_extensions:
            err_console.print("[bold red]Error:[/] --extensions value is empty.")
            raise typer.Exit(code=1)

    # ── Scan ─────────────────────────────────────────────────────────────────
    with console.status("[bold cyan]Scanning files…", spinner="dots"):
        try:
            files = list(
                scan_directory(
                    path,
                    max_size_bytes=max_size_bytes,
                    include_extensions=include_extensions,
                    use_gitignore=use_gitignore,
                )
            )
        except (FileNotFoundError, NotADirectoryError) as exc:
            err_console.print(f"[bold red]Error:[/] {exc}")
            raise typer.Exit(code=1) from exc

    if not files:
        err_console.print(
            Panel(
                "[yellow]No files found.[/] Check the path or ignore rules.",
                title="prompt-pack",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=0)

    # ── Build Markdown ────────────────────────────────────────────────────────
    with console.status("[bold cyan]Building Markdown…", spinner="dots"):
        result = build_markdown(files, root=path)
    markdown = result.markdown

    # ── Stdout mode ───────────────────────────────────────────────────────────
    if stdout:
        # Write raw UTF-8 to stdout.buffer to avoid terminal encoding issues
        sys.stdout.buffer.write(markdown.encode("utf-8"))
        if not no_clipboard:
            try:
                import pyperclip  # noqa: PLC0415

                pyperclip.copy(markdown)
            except Exception:  # noqa: BLE001
                pass
        return

    # ── Write file ────────────────────────────────────────────────────────────
    out_path = output or (Path.cwd() / "prompt_output.md")
    try:
        out_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        err_console.print(f"[bold red]Error writing file:[/] {exc}")
        raise typer.Exit(code=1) from exc

    # ── Clipboard ─────────────────────────────────────────────────────────────
    clipboard_ok = False
    if not no_clipboard:
        try:
            import pyperclip  # noqa: PLC0415

            pyperclip.copy(markdown)
            clipboard_ok = True
        except Exception:  # noqa: BLE001
            pass  # Clipboard failure is non-fatal

    # ── Summary panel ─────────────────────────────────────────────────────────
    clipboard_status = (
        "[green]✓ copied to clipboard[/]"
        if clipboard_ok
        else "[dim]clipboard unavailable[/]"
    )

    summary = Text.assemble(
        ("Files packed: ", "bold"), (f"{result.file_count}\n", "cyan"),
        ("Lines: ", "bold"), (f"{result.total_lines:,}\n", "cyan"),
        ("~Tokens: ", "bold"), (f"{result.estimated_tokens:,}\n", "cyan"),
        ("Output: ", "bold"), (f"{out_path}\n", "cyan"),
        ("Clipboard: ", "bold"),
    )
    summary.append_text(Text.from_markup(clipboard_status))

    console.print(
        Panel(summary, title="[bold green]prompt-pack[/] done ✓", border_style="green")
    )


if __name__ == "__main__":  # pragma: no cover
    app()
