"""Tests for prompt_pack.scanner."""

from __future__ import annotations

import pytest

from prompt_pack.scanner import scan_directory


class TestScanDirectory:
    def test_returns_included_files_only(self, tmp_tree):
        """Only main.py, helpers.py, data.json should be returned."""
        results = list(scan_directory(tmp_tree))
        names = {p.name for p in results}
        assert names == {"main.py", "helpers.py", "data.json"}

    def test_excludes_ignored_directories(self, tmp_tree):
        results = list(scan_directory(tmp_tree))
        paths_str = [str(p) for p in results]
        assert not any("__pycache__" in s for s in paths_str)
        assert not any("node_modules" in s for s in paths_str)

    def test_excludes_ignored_extensions(self, tmp_tree):
        results = list(scan_directory(tmp_tree))
        assert not any(p.suffix == ".png" for p in results)

    def test_excludes_oversized_files(self, tmp_tree):
        results = list(scan_directory(tmp_tree))
        assert not any(p.name == "big_file.txt" for p in results)

    def test_output_is_sorted(self, tmp_tree):
        """Files should come out in a deterministic order."""
        results1 = list(scan_directory(tmp_tree))
        results2 = list(scan_directory(tmp_tree))
        assert results1 == results2

    def test_raises_for_nonexistent_path(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError):
            list(scan_directory(missing))

    def test_raises_for_file_instead_of_dir(self, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1", encoding="utf-8")
        with pytest.raises(NotADirectoryError):
            list(scan_directory(f))

    def test_empty_directory_returns_nothing(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert list(scan_directory(empty)) == []

    def test_custom_max_size_respected(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        small = root / "small.py"
        small.write_bytes(b"x" * 100)
        medium = root / "medium.py"
        medium.write_bytes(b"y" * 2048)

        # With 1 KB limit, only small.py should appear
        results = list(scan_directory(root, max_size_bytes=1024))
        assert {p.name for p in results} == {"small.py"}

    def test_generator_is_lazy(self, tmp_tree):
        """scan_directory must return a generator, not a list."""
        import types
        result = scan_directory(tmp_tree)
        assert isinstance(result, types.GeneratorType)
