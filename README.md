# prompt-pack

> Pack your codebase into a single Markdown file, ready to paste into any AI.

## Install

```bash
pipx install .
```

## Usage

```bash
prompt-pack ./src
prompt-pack ./src --output my_prompt.md
prompt-pack ./src --no-clipboard
prompt-pack ./src --max-size 200   # max file size in KB
```

Running the command will:
1. Scan the target directory recursively, ignoring binaries, `node_modules`, `__pycache__`, and large files
2. Build a single Markdown file with every included file formatted in a fenced code block
3. Write the result to `prompt_output.md` (or `--output`)
4. Copy the result to your clipboard automatically

## Features

- Recursive directory scan with smart ignore rules
- Language-aware code fences (Python, TypeScript, Go, Rust, and 40+ others)
- Token estimate in the output header
- `.promptpackignore` support for custom ignore rules *(coming in v0.2)*
- Cross-platform clipboard support

## Development

```bash
git clone https://github.com/Mendoncaa/MakePromptEasy
cd MakePromptEasy
python -m pip install -e ".[dev]"
pytest --cov=prompt_pack
ruff check src tests
```
