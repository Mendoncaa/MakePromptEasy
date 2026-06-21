"""End-to-end integration tests for the prompt-pack CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from prompt_pack.cli import app

runner = CliRunner()


def _make_tree(tmp_path: Path) -> Path:
    """Create a small source tree for integration tests."""
    root = tmp_path / "project"
    root.mkdir()
    (root / "main.py").write_text("def main(): pass\n", encoding="utf-8")
    src = root / "src"
    src.mkdir()
    (src / "utils.py").write_text("def helper(): return 42\n", encoding="utf-8")
    (root / "README.md").write_text("# My Project\n", encoding="utf-8")
    return root


class TestCLIIntegration:
    def test_basic_run_creates_output_file(self, tmp_path):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        result = runner.invoke(app, [str(root), "--output", str(out), "--no-clipboard"])
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_output_contains_code_fences(self, tmp_path):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        runner.invoke(app, [str(root), "--output", str(out), "--no-clipboard"])
        content = out.read_text(encoding="utf-8")
        assert "```python" in content
        assert "def main" in content

    def test_output_contains_header(self, tmp_path):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        runner.invoke(app, [str(root), "--output", str(out), "--no-clipboard"])
        content = out.read_text(encoding="utf-8")
        assert "# Prompt Pack" in content
        assert "**Files:**" in content

    def test_nonexistent_path_exits_with_error(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        result = runner.invoke(app, [str(missing), "--no-clipboard"])
        assert result.exit_code != 0

    def test_max_size_flag_filters_large_files(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        small = root / "small.py"
        small.write_bytes(b"x" * 100)
        large = root / "large.py"
        large.write_bytes(b"y" * (200 * 1024))  # 200 KB

        out = tmp_path / "out.md"
        # max-size in KB; set to 1 KB so large.py is excluded
        runner.invoke(
            app,
            [str(root), "--output", str(out), "--no-clipboard", "--max-size", "1"],
        )
        content = out.read_text(encoding="utf-8")
        assert "small.py" in content
        assert "large.py" not in content

    def test_help_exits_cleanly(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "prompt-pack" in result.output.lower() or "path" in result.output.lower()

    def test_summary_panel_shown(self, tmp_path):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        result = runner.invoke(app, [str(root), "--output", str(out), "--no-clipboard"])
        assert result.exit_code == 0
        # Rich panel content should be in output
        assert "Files packed" in result.output or "done" in result.output.lower()

    def test_empty_directory_shows_no_files_warning(self, tmp_path):
        empty = tmp_path / "empty_project"
        empty.mkdir()
        result = runner.invoke(app, [str(empty), "--no-clipboard"])
        assert result.exit_code == 0
        assert "No files found" in result.output

    def test_stdout_mode_prints_markdown(self, tmp_path):
        root = _make_tree(tmp_path)
        result = runner.invoke(app, [str(root), "--stdout", "--no-clipboard"])
        assert result.exit_code == 0
        assert "# Prompt Pack" in result.output

    def test_stdout_mode_writes_no_file(self, tmp_path):
        root = _make_tree(tmp_path)
        result = runner.invoke(app, [str(root), "--stdout", "--no-clipboard"])
        assert result.exit_code == 0
        # Default output file should NOT be created
        assert not (tmp_path / "prompt_output.md").exists()

    def test_scan_error_handled_gracefully(self, tmp_path, monkeypatch):
        import prompt_pack.cli as cli_module

        def bad_scan(*args, **kwargs):
            raise FileNotFoundError("Mock scan error")

        monkeypatch.setattr(cli_module, "scan_directory", bad_scan)
        result = runner.invoke(app, [str(tmp_path), "--no-clipboard"])
        assert result.exit_code == 1

    def test_write_error_handled_gracefully(self, tmp_path, monkeypatch):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"

        original_write = Path.write_text

        def bad_write(self, *args, **kwargs):
            if self == out:
                raise OSError("Disk full")
            return original_write(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", bad_write)
        result = runner.invoke(
            app, [str(root), "--output", str(out), "--no-clipboard"]
        )
        assert result.exit_code == 1

    def test_stdout_mode_with_clipboard(self, tmp_path, monkeypatch):
        import pyperclip

        copied: list[str] = []
        monkeypatch.setattr(pyperclip, "copy", lambda text: copied.append(text))
        root = _make_tree(tmp_path)
        result = runner.invoke(app, [str(root), "--stdout"])
        assert result.exit_code == 0
        assert len(copied) == 1

    def test_stdout_mode_clipboard_failure_non_fatal(self, tmp_path, monkeypatch):
        import pyperclip

        monkeypatch.setattr(
            pyperclip, "copy", lambda text: (_ for _ in ()).throw(Exception("fail"))
        )
        root = _make_tree(tmp_path)
        result = runner.invoke(app, [str(root), "--stdout"])
        assert result.exit_code == 0

    def test_clipboard_success_shows_copied(self, tmp_path, monkeypatch):
        import pyperclip

        copied: list[str] = []
        monkeypatch.setattr(pyperclip, "copy", lambda text: copied.append(text))
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        result = runner.invoke(app, [str(root), "--output", str(out)])
        assert result.exit_code == 0
        assert len(copied) == 1
        assert "copied to clipboard" in result.output

    def test_clipboard_failure_is_non_fatal(self, tmp_path, monkeypatch):
        import pyperclip

        monkeypatch.setattr(
            pyperclip, "copy", lambda text: (_ for _ in ()).throw(Exception("No CB"))
        )
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        result = runner.invoke(app, [str(root), "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()


class TestCLIVersion:
    def test_version_flag_exits_cleanly(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_flag_short(self):
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0

    def test_version_output_contains_version_string(self):
        from prompt_pack import __version__

        result = runner.invoke(app, ["--version"])
        assert __version__ in result.output


class TestCLIExtensions:
    def test_extensions_filters_to_python_only(self, tmp_path):
        root = tmp_path / "proj"
        root.mkdir()
        (root / "main.py").write_text("x=1\n", encoding="utf-8")
        (root / "index.ts").write_text("const x=1;\n", encoding="utf-8")
        out = tmp_path / "out.md"
        runner.invoke(
            app,
            [str(root), "--extensions", "py", "--output", str(out), "--no-clipboard"],
        )
        content = out.read_text(encoding="utf-8")
        assert "main.py" in content
        assert "index.ts" not in content

    def test_extensions_accepts_dot_prefix(self, tmp_path):
        root = tmp_path / "proj"
        root.mkdir()
        (root / "app.py").write_text("x=1\n", encoding="utf-8")
        (root / "app.js").write_text("const x=1;\n", encoding="utf-8")
        out = tmp_path / "out.md"
        runner.invoke(
            app,
            [str(root), "--extensions", ".py", "--output", str(out), "--no-clipboard"],
        )
        content = out.read_text(encoding="utf-8")
        assert "app.py" in content
        assert "app.js" not in content

    def test_extensions_multiple_comma_separated(self, tmp_path):
        root = tmp_path / "proj"
        root.mkdir()
        (root / "a.py").write_text("x=1\n", encoding="utf-8")
        (root / "b.ts").write_text("const x=1;\n", encoding="utf-8")
        (root / "c.go").write_text("package main\n", encoding="utf-8")
        (root / "d.css").write_text("body{}\n", encoding="utf-8")
        out = tmp_path / "out.md"
        runner.invoke(
            app,
            [
                str(root),
                "--extensions",
                "py,ts",
                "--output",
                str(out),
                "--no-clipboard",
            ],
        )
        content = out.read_text(encoding="utf-8")
        assert "a.py" in content
        assert "b.ts" in content
        assert "c.go" not in content
        assert "d.css" not in content

    def test_extensions_empty_value_exits_with_error(self, tmp_path):
        root = tmp_path / "proj"
        root.mkdir()
        result = runner.invoke(
            app, [str(root), "--extensions", ",,,", "--no-clipboard"]
        )
        assert result.exit_code == 1


class TestCLIStdoutOutputMutex:
    def test_stdout_with_output_warns_user(self, tmp_path):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        result = runner.invoke(
            app, [str(root), "--stdout", "--output", str(out), "--no-clipboard"]
        )
        assert result.exit_code == 0
        assert "Warning" in result.output or "ignored" in result.output.lower()

    def test_stdout_with_output_does_not_write_file(self, tmp_path):
        root = _make_tree(tmp_path)
        out = tmp_path / "out.md"
        runner.invoke(
            app, [str(root), "--stdout", "--output", str(out), "--no-clipboard"]
        )
        assert not out.exists()

