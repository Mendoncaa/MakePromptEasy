"""Shared pytest fixtures for prompt-pack tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def tmp_tree(tmp_path):
    """Create a deterministic file-tree for scanner/formatter tests.

    Structure:
        root/
          main.py          (small Python file)
          utils/
            helpers.py     (small Python file)
            data.json      (small JSON)
          assets/
            logo.png       (binary-ish, ignored by extension)
          __pycache__/
            main.cpython-311.pyc  (ignored dir)
          node_modules/
            lib.js         (ignored dir)
          big_file.txt     (>500 KB, ignored by size)
    """
    root = tmp_path / "root"
    root.mkdir()

    # Included files
    (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
    utils = root / "utils"
    utils.mkdir()
    (utils / "helpers.py").write_text("def helper(): pass\n", encoding="utf-8")
    (utils / "data.json").write_text('{"key": "value"}\n', encoding="utf-8")

    # Ignored by extension
    assets = root / "assets"
    assets.mkdir()
    (assets / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    # Ignored directory
    cache = root / "__pycache__"
    cache.mkdir()
    (cache / "main.cpython-311.pyc").write_bytes(b"\x00\x00\x00\x00")

    node_modules = root / "node_modules"
    node_modules.mkdir()
    (node_modules / "lib.js").write_text("module.exports = {};", encoding="utf-8")

    # Ignored by size (600 KB)
    big = root / "big_file.txt"
    big.write_bytes(b"x" * (600 * 1024))

    return root
