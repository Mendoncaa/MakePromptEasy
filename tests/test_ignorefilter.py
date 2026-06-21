"""Tests for prompt_pack.ignorefilter."""

from __future__ import annotations

from pathlib import Path

from prompt_pack.ignorefilter import (
    IGNORE_FILE_NAME,
    load_ignore_patterns,
    matches_ignore_pattern,
)

# ── load_ignore_patterns ──────────────────────────────────────────────────────

class TestLoadIgnorePatterns:
    def test_returns_empty_when_file_absent(self, tmp_path):
        assert load_ignore_patterns(tmp_path) == []

    def test_parses_simple_patterns(self, tmp_path):
        (tmp_path / IGNORE_FILE_NAME).write_text("*.log\n*.tmp\n", encoding="utf-8")
        assert load_ignore_patterns(tmp_path) == ["*.log", "*.tmp"]

    def test_ignores_comment_lines(self, tmp_path):
        content = "# This is a comment\n*.log\n# another comment\n*.tmp\n"
        (tmp_path / IGNORE_FILE_NAME).write_text(content, encoding="utf-8")
        assert load_ignore_patterns(tmp_path) == ["*.log", "*.tmp"]

    def test_ignores_blank_lines(self, tmp_path):
        content = "\n*.log\n\n\n*.tmp\n"
        (tmp_path / IGNORE_FILE_NAME).write_text(content, encoding="utf-8")
        assert load_ignore_patterns(tmp_path) == ["*.log", "*.tmp"]

    def test_strips_whitespace(self, tmp_path):
        content = "  *.log  \n  *.tmp  \n"
        (tmp_path / IGNORE_FILE_NAME).write_text(content, encoding="utf-8")
        assert load_ignore_patterns(tmp_path) == ["*.log", "*.tmp"]

    def test_empty_file_returns_empty(self, tmp_path):
        (tmp_path / IGNORE_FILE_NAME).write_text("", encoding="utf-8")
        assert load_ignore_patterns(tmp_path) == []

    def test_only_comments_returns_empty(self, tmp_path):
        text = "# ignore me\n# me too\n"
        (tmp_path / IGNORE_FILE_NAME).write_text(text, encoding="utf-8")
        assert load_ignore_patterns(tmp_path) == []

    def test_oserror_on_read_returns_empty(self, tmp_path, monkeypatch):
        """If the ignore file can't be read, return [] gracefully."""
        (tmp_path / IGNORE_FILE_NAME).write_text("*.log\n", encoding="utf-8")

        def bad_read_text(self, *args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "read_text", bad_read_text)
        assert load_ignore_patterns(tmp_path) == []

# ── matches_ignore_pattern ────────────────────────────────────────────────────

class TestMatchesIgnorePattern:
    def _make(self, tmp_path: Path, name: str) -> Path:
        p = tmp_path / name
        p.write_text("x", encoding="utf-8")
        return p

    def test_empty_patterns_never_match(self, tmp_path):
        f = self._make(tmp_path, "app.log")
        assert matches_ignore_pattern(f, tmp_path, []) is False

    def test_wildcard_extension_matches_by_name(self, tmp_path):
        f = self._make(tmp_path, "app.log")
        assert matches_ignore_pattern(f, tmp_path, ["*.log"]) is True

    def test_wildcard_extension_non_matching(self, tmp_path):
        f = self._make(tmp_path, "app.py")
        assert matches_ignore_pattern(f, tmp_path, ["*.log"]) is False

    def test_exact_filename_match(self, tmp_path):
        f = self._make(tmp_path, "secrets.env")
        assert matches_ignore_pattern(f, tmp_path, ["secrets.env"]) is True

    def test_subdirectory_pattern_matches(self, tmp_path):
        sub = tmp_path / "logs"
        sub.mkdir()
        f = sub / "app.log"
        f.write_text("x", encoding="utf-8")
        # "logs/*.log" matches "logs/app.log"
        assert matches_ignore_pattern(f, tmp_path, ["logs/*.log"]) is True

    def test_subdirectory_pattern_no_match_outside(self, tmp_path):
        f = self._make(tmp_path, "app.log")
        # "logs/*.log" should NOT match "app.log" at root
        assert matches_ignore_pattern(f, tmp_path, ["logs/*.log"]) is False

    def test_name_pattern_matches_in_subdirectory(self, tmp_path):
        sub = tmp_path / "deep" / "nested"
        sub.mkdir(parents=True)
        f = sub / "debug.log"
        f.write_text("x", encoding="utf-8")
        # "*.log" matches by name anywhere in tree
        assert matches_ignore_pattern(f, tmp_path, ["*.log"]) is True

    def test_path_outside_root_returns_false(self, tmp_path):
        other = tmp_path.parent / "other.py"
        assert matches_ignore_pattern(other, tmp_path, ["*.py"]) is False

    def test_multiple_patterns_any_match(self, tmp_path):
        f = self._make(tmp_path, "app.tmp")
        assert matches_ignore_pattern(f, tmp_path, ["*.log", "*.tmp"]) is True


# ── Integration with scanner ──────────────────────────────────────────────────

class TestScannerWithIgnoreFile:
    def test_promptpackignore_excludes_log_files(self, tmp_path):
        from prompt_pack.scanner import scan_directory

        (tmp_path / IGNORE_FILE_NAME).write_text("*.log\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "app.log").write_text("log entry\n", encoding="utf-8")

        results = {p.name for p in scan_directory(tmp_path)}
        assert "main.py" in results
        assert "app.log" not in results
        # .promptpackignore itself is NOT in DEFAULT_IGNORE_FILENAMES,
        # so it appears in results
        assert IGNORE_FILE_NAME in results

    def test_promptpackignore_excludes_directory(self, tmp_path):
        from prompt_pack.scanner import scan_directory

        (tmp_path / IGNORE_FILE_NAME).write_text("secrets/\n", encoding="utf-8")
        secrets = tmp_path / "secrets"
        secrets.mkdir()
        (secrets / "key.pem").write_text("secret", encoding="utf-8")
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

        results = {p.name for p in scan_directory(tmp_path)}
        assert "main.py" in results
        assert "key.pem" not in results

    def test_explicit_patterns_override_file(self, tmp_path):
        from prompt_pack.scanner import scan_directory

        # .promptpackignore says exclude *.log, but we pass explicit empty patterns
        (tmp_path / IGNORE_FILE_NAME).write_text("*.log\n", encoding="utf-8")
        (tmp_path / "app.log").write_text("entry\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x\n", encoding="utf-8")

        results = {p.name for p in scan_directory(tmp_path, ignore_patterns=[])}
        assert "app.log" in results  # Not excluded — explicit empty list used


# ── .gitignore support ────────────────────────────────────────────────────────

class TestGitignoreSupport:
    def test_load_gitignore_returns_none_when_absent(self, tmp_path):
        from prompt_pack.ignorefilter import load_gitignore

        assert load_gitignore(tmp_path) is None

    def test_load_gitignore_parses_rules(self, tmp_path):
        from prompt_pack.ignorefilter import load_gitignore

        (tmp_path / ".gitignore").write_text("*.log\nbuild/\n", encoding="utf-8")
        spec = load_gitignore(tmp_path)
        assert spec is not None
        assert spec.match_file("app.log")
        assert spec.match_file("build/")
        assert not spec.match_file("main.py")

    def test_use_gitignore_excludes_matching_files(self, tmp_path):
        from prompt_pack.scanner import scan_directory

        (tmp_path / ".gitignore").write_text("*.log\ndist/\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x=1\n", encoding="utf-8")
        (tmp_path / "app.log").write_text("log\n", encoding="utf-8")
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "bundle.js").write_text("js\n", encoding="utf-8")

        results = {p.name for p in scan_directory(tmp_path, use_gitignore=True)}
        assert "main.py" in results
        assert "app.log" not in results
        assert "bundle.js" not in results

    def test_use_gitignore_false_ignores_gitignore(self, tmp_path):
        from prompt_pack.scanner import scan_directory

        (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("x=1\n", encoding="utf-8")
        (tmp_path / "app.log").write_text("log\n", encoding="utf-8")

        results = {p.name for p in scan_directory(tmp_path, use_gitignore=False)}
        assert "main.py" in results
        assert "app.log" in results  # Not excluded when flag is off
