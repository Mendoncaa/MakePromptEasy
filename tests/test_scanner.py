"""Tests for prompt_pack.scanner."""

from __future__ import annotations

from pathlib import Path

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

    def test_symlinks_are_skipped(self, tmp_path, monkeypatch):
        """Symlinks must never be followed to avoid infinite loops."""
        root = tmp_path / "root"
        root.mkdir()
        real = root / "real.py"
        real.write_text("x = 1\n", encoding="utf-8")
        fake_link = root / "link.py"
        fake_link.write_text("x = 1\n", encoding="utf-8")

        original_is_symlink = Path.is_symlink

        def mock_is_symlink(self: Path) -> bool:
            if self.name == "link.py":
                return True
            return original_is_symlink(self)

        monkeypatch.setattr(Path, "is_symlink", mock_is_symlink)
        results = {p.name for p in scan_directory(root)}
        assert "real.py" in results
        assert "link.py" not in results

    def test_permission_error_on_subdir_is_skipped(self, tmp_path, monkeypatch):
        """Directories that raise PermissionError are silently skipped."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "accessible.py").write_text("x = 1\n", encoding="utf-8")
        restricted = root / "restricted"
        restricted.mkdir()
        (restricted / "secret.py").write_text("secret\n", encoding="utf-8")

        original_iterdir = Path.iterdir

        def mock_iterdir(self: Path):
            if self.name == "restricted":
                raise PermissionError("Access denied")
            return original_iterdir(self)

        monkeypatch.setattr(Path, "iterdir", mock_iterdir)
        results = {p.name for p in scan_directory(root)}
        assert "accessible.py" in results
        assert "secret.py" not in results
