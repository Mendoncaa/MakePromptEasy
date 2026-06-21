# prompt-pack

[![CI](https://github.com/Mendoncaa/MakePromptEasy/actions/workflows/ci.yml/badge.svg)](https://github.com/Mendoncaa/MakePromptEasy/actions/workflows/ci.yml)

> Pack your codebase into a single Markdown file, ready to paste into any AI.

**prompt-pack** recursively scans a directory, ignores binaries and noise (`node_modules`, `__pycache__`, large files…), and generates one clean Markdown document with every source file in a fenced code block — token estimate included.

---

## Install

```bash
pipx install git+https://github.com/Mendoncaa/MakePromptEasy
```

Or for development:

```bash
git clone https://github.com/Mendoncaa/MakePromptEasy
cd MakePromptEasy
python -m pip install -e ".[dev]"
```

---

## Usage

```bash
# Pack ./src → prompt_output.md + copy to clipboard
prompt-pack ./src

# Custom output file
prompt-pack ./src --output my_prompt.md

# Print to stdout (pipe-friendly)
prompt-pack ./src --stdout

# Don't copy to clipboard
prompt-pack ./src --no-clipboard

# Raise the per-file size limit to 1 MB
prompt-pack ./src --max-size 1024
```

The output file contains:

- A header with source path, date, file count, line count and estimated tokens
- A table of contents linking to each file section
- Every file as a fenced code block with language syntax highlighting
- A footer summary

---

## .promptpackignore

Place a `.promptpackignore` file in the directory you're packing to exclude additional files or folders.  
Uses Unix shell-style glob patterns (one per line). Lines starting with `#` are comments.

```gitignore
# Exclude all log files
*.log

# Exclude the fixtures folder
tests/fixtures/

# Exclude a specific file
secrets.env
```

See [`.promptpackignore.example`](.promptpackignore.example) for a full example.

---

## What gets ignored by default

| Category | Examples |
|---|---|
| Build/cache dirs | `__pycache__`, `node_modules`, `.venv`, `dist`, `.git` |
| Binary extensions | `.png`, `.jpg`, `.exe`, `.zip`, `.pyc`, `.dll`, `.pdf` |
| Lock files | `package-lock.json`, `yarn.lock`, `poetry.lock` |
| Large files | anything above 500 KB (configurable via `--max-size`) |

---

## Options

```
Arguments:
  path  Directory to pack. [required]

Options:
  -o, --output PATH     Output file. Defaults to prompt_output.md.
  --stdout              Print output to stdout instead of writing a file.
  --no-clipboard        Skip copying to clipboard.
  --max-size INTEGER    Max file size to include, in KB. [default: 500]
  --help                Show this message and exit.
```

---

## Development

```bash
# Run tests with coverage
pytest --cov=prompt_pack --cov-report=term-missing

# Lint
ruff check src tests

# Auto-fix lint
ruff check src tests --fix
```

---

## License

MIT
