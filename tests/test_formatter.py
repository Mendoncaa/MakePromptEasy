"""Tests for prompt_pack.formatter."""

from __future__ import annotations

from pathlib import Path

from prompt_pack.formatter import _estimate_tokens, _language_hint, build_markdown


class TestLanguageHint:
    def test_python(self, tmp_path):
        assert _language_hint(tmp_path / "app.py") == "python"

    def test_typescript(self, tmp_path):
        assert _language_hint(tmp_path / "index.ts") == "typescript"

    def test_yaml(self, tmp_path):
        assert _language_hint(tmp_path / "config.yml") == "yaml"

    def test_unknown_extension(self, tmp_path):
        assert _language_hint(tmp_path / "file.xyz") == ""

    def test_no_extension(self, tmp_path):
        assert _language_hint(tmp_path / "Makefile") == "makefile"

    def test_case_insensitive(self, tmp_path):
        assert _language_hint(tmp_path / "Script.PY") == "python"


class TestEstimateTokens:
    def test_empty_string(self):
        assert _estimate_tokens("") == 1  # Minimum of 1

    def test_four_chars_is_one_token(self):
        assert _estimate_tokens("abcd") == 1

    def test_larger_text(self):
        text = "a" * 4000
        assert _estimate_tokens(text) == 1000


class TestBuildMarkdown:
    def _make_files(self, tmp_path, contents: dict[str, str]) -> list[Path]:
        files = []
        for name, text in contents.items():
            p = tmp_path / name
            p.write_text(text, encoding="utf-8")
            files.append(p)
        return files

    def test_header_present(self, tmp_path):
        files = self._make_files(tmp_path, {"app.py": "x = 1\n"})
        md = build_markdown(files, root=tmp_path)
        assert "# Prompt Pack" in md

    def test_file_count_in_header(self, tmp_path):
        files = self._make_files(tmp_path, {"a.py": "pass\n", "b.py": "pass\n"})
        md = build_markdown(files, root=tmp_path)
        assert "**Files:** 2" in md

    def test_code_fences_present(self, tmp_path):
        files = self._make_files(tmp_path, {"script.py": "print('hi')\n"})
        md = build_markdown(files, root=tmp_path)
        assert "```python" in md
        assert "print('hi')" in md

    def test_relative_path_in_output(self, tmp_path):
        sub = tmp_path / "src"
        sub.mkdir()
        f = sub / "utils.py"
        f.write_text("def foo(): pass\n", encoding="utf-8")
        md = build_markdown([f], root=tmp_path)
        assert "src/utils.py" in md

    def test_footer_present(self, tmp_path):
        files = self._make_files(tmp_path, {"app.py": "x = 1\n"})
        md = build_markdown(files, root=tmp_path)
        assert "prompt-pack" in md.lower()

    def test_empty_file_list(self, tmp_path):
        md = build_markdown([], root=tmp_path)
        assert "**Files:** 0" in md

    def test_multiple_languages(self, tmp_path):
        files = self._make_files(
            tmp_path,
            {"main.py": "x=1\n", "index.ts": "const x=1;\n", "style.css": "body{}\n"},
        )
        md = build_markdown(files, root=tmp_path)
        assert "```python" in md
        assert "```typescript" in md
        assert "```css" in md

    def test_token_estimate_in_header(self, tmp_path):
        files = self._make_files(tmp_path, {"app.py": "a" * 400})
        md = build_markdown(files, root=tmp_path)
        assert "Estimated tokens" in md

    def test_table_of_contents_present(self, tmp_path):
        files = self._make_files(tmp_path, {"app.py": "x = 1\n"})
        md = build_markdown(files, root=tmp_path)
        assert "## Table of Contents" in md
