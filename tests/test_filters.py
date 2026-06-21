"""Tests for prompt_pack.filters."""

from __future__ import annotations

from pathlib import Path

import pytest

from prompt_pack.filters import is_ignored_dir, should_ignore

# ── is_ignored_dir ────────────────────────────────────────────────────────────

class TestIsIgnoredDir:
    def test_pycache_dir_itself_ignored(self, tmp_path):
        # _walk passes the directory entry itself, not a file inside it
        p = tmp_path / "__pycache__"
        assert is_ignored_dir(p) is True

    def test_node_modules_dir_itself_ignored(self, tmp_path):
        p = tmp_path / "node_modules"
        assert is_ignored_dir(p) is True

    def test_venv_dir_itself_ignored(self, tmp_path):
        p = tmp_path / ".venv"
        assert is_ignored_dir(p) is True

    def test_normal_dir_not_ignored(self, tmp_path):
        p = tmp_path / "src"
        assert is_ignored_dir(p) is False

    def test_egg_info_glob_pattern_on_dir(self, tmp_path):
        # Only the directory entry itself is checked (not a file inside)
        p = tmp_path / "my_package.egg-info"
        assert is_ignored_dir(p) is True

    def test_no_false_positive_from_ancestor_path(self, tmp_path):
        """A file/dir inside a project that lives under an 'env' ancestor must
        not be incorrectly excluded because 'env' appears in the absolute path."""
        # Simulate project at /tmp/.../env/project/src/utils.py
        env_ancestor = tmp_path / "env" / "project" / "src"
        env_ancestor.mkdir(parents=True)
        p = env_ancestor / "utils.py"
        # Only the name "utils.py" is checked — must NOT be excluded
        assert is_ignored_dir(p) is False

    def test_no_false_positive_for_src_inside_env_project(self, tmp_path):
        """The 'src' directory inside /env/project/ must not be pruned."""
        src_under_env = tmp_path / "env" / "project" / "src"
        src_under_env.mkdir(parents=True)
        assert is_ignored_dir(src_under_env) is False


# ── should_ignore — extension ─────────────────────────────────────────────────

class TestShouldIgnoreExtension:
    @pytest.mark.parametrize(
        "ext", [".png", ".jpg", ".gif", ".exe", ".zip", ".pyc", ".dll"]
    )
    def test_binary_extensions_ignored(self, tmp_path, ext):
        p = tmp_path / f"file{ext}"
        p.write_bytes(b"\x00")
        assert should_ignore(p) is True

    def test_python_file_not_ignored(self, tmp_path):
        p = tmp_path / "main.py"
        p.write_text("print('hello')", encoding="utf-8")
        assert should_ignore(p) is False

    def test_markdown_not_ignored(self, tmp_path):
        p = tmp_path / "README.md"
        p.write_text("# Hello", encoding="utf-8")
        assert should_ignore(p) is False


# ── should_ignore — filename ──────────────────────────────────────────────────

class TestShouldIgnoreFilename:
    def test_package_lock_ignored(self, tmp_path):
        p = tmp_path / "package-lock.json"
        p.write_text("{}", encoding="utf-8")
        assert should_ignore(p) is True

    def test_yarn_lock_ignored(self, tmp_path):
        p = tmp_path / "yarn.lock"
        p.write_text("# yarn", encoding="utf-8")
        assert should_ignore(p) is True

    def test_gitignore_ignored(self, tmp_path):
        p = tmp_path / ".gitignore"
        p.write_text("*.pyc", encoding="utf-8")
        assert should_ignore(p) is True


# ── should_ignore — size ──────────────────────────────────────────────────────

class TestShouldIgnoreSize:
    def test_file_above_max_size_ignored(self, tmp_path):
        big = tmp_path / "big.txt"
        big.write_bytes(b"x" * (600 * 1024))
        assert should_ignore(big, max_size_bytes=500 * 1024) is True

    def test_file_at_max_size_included(self, tmp_path):
        exact = tmp_path / "exact.txt"
        exact.write_bytes(b"x" * (500 * 1024))
        assert should_ignore(exact, max_size_bytes=500 * 1024) is False

    def test_file_below_max_size_included(self, tmp_path):
        small = tmp_path / "small.py"
        small.write_text("x = 1", encoding="utf-8")
        assert should_ignore(small, max_size_bytes=500 * 1024) is False

    def test_custom_max_size_respected(self, tmp_path):
        p = tmp_path / "medium.txt"
        p.write_bytes(b"y" * 1024)  # 1 KB
        assert should_ignore(p, max_size_bytes=512) is True  # 512 bytes limit
        assert should_ignore(p, max_size_bytes=2048) is False  # 2 KB limit

    def test_stat_oserror_causes_ignore(self, tmp_path, monkeypatch):
        """If stat() raises OSError the file should be excluded (safe default)."""
        f = tmp_path / "mystery.py"
        f.write_text("x = 1", encoding="utf-8")

        def bad_stat(self, *args, **kwargs):
            raise OSError("stat failed")

        monkeypatch.setattr(Path, "stat", bad_stat)
        assert should_ignore(f) is True
