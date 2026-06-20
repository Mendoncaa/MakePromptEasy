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
