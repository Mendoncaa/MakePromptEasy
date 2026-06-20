"""Tests for prompt_pack.filters."""

from __future__ import annotations

import pytest  # noqa: I001

from prompt_pack.filters import is_ignored_dir, should_ignore

# ── is_ignored_dir ────────────────────────────────────────────────────────────

class TestIsIgnoredDir:
    def test_pycache_ignored(self, tmp_path):
        p = tmp_path / "__pycache__" / "foo.pyc"
        assert is_ignored_dir(p) is True

    def test_node_modules_ignored(self, tmp_path):
        p = tmp_path / "node_modules" / "lodash" / "index.js"
        assert is_ignored_dir(p) is True

    def test_venv_ignored(self, tmp_path):
        p = tmp_path / ".venv" / "lib" / "python3.11" / "site.py"
        assert is_ignored_dir(p) is True

    def test_normal_path_not_ignored(self, tmp_path):
        p = tmp_path / "src" / "app.py"
        assert is_ignored_dir(p) is False

    def test_egg_info_glob_pattern(self, tmp_path):
        p = tmp_path / "my_package.egg-info" / "PKG-INFO"
        assert is_ignored_dir(p) is True


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
