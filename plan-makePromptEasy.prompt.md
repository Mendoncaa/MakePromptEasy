# Plan: MakePromptEasy — `prompt-pack` CLI

**TL;DR** — CLI em Python que aceita `prompt-pack ./src` e gera um ficheiro Markdown único com todo o código da pasta formatado em blocos de código, pronto para colar em qualquer IA. Adicionalmente, copia automaticamente para o clipboard. Distribuído via `pipx`. Repositório `Mendoncaa/MakePromptEasy` com commit/push automático em cada etapa fechada.

---

## 1. Tech Stack

| Componente | Escolha | Justificação |
|---|---|---|
| Runtime | Python 3.11+ | Target (devs de IA) já têm Python; `pathlib` é ideal para recursividade de ficheiros |
| CLI Framework | `typer` + `rich` | Auto-help, validação de args, output colorido sem esforço |
| Clipboard | `pyperclip` | Cross-platform (Win/Mac/Linux) |
| Linting | `ruff` | Ultra-rápido, substitui black + flake8 |
| Testes | `pytest` + `pytest-cov` | Standard, suporte a fixtures e cobertura |
| Packaging | `pyproject.toml` + `hatchling` | Moderno, sem `setup.py` |
| Git/GitHub | `gh` CLI | `gh repo create` + `git` nativo |

**Eficiência:** Zero LLM no motor — a "inteligência" é filtragem por extensão e tamanho **antes** de abrir qualquer ficheiro (lazy evaluation com generators), garantindo consumo mínimo de recursos.

---

## 2. Arquitetura de Pastas

```
MakePromptEasy/
├── src/
│   └── prompt_pack/
│       ├── __init__.py
│       ├── cli.py          ← Entry point (typer app, orquestra tudo)
│       ├── scanner.py      ← Travessia recursiva (generator de Paths)
│       ├── filters.py      ← Regras de ignorar (extensão, tamanho, padrões)
│       ├── formatter.py    ← Constrói o Markdown final
│       └── config.py       ← Constantes, extensões ignoradas por default
├── tests/
│   ├── conftest.py         ← Fixtures partilhadas (tmp_path com ficheiros fake)
│   ├── test_scanner.py
│   ├── test_filters.py
│   └── test_formatter.py
├── pyproject.toml          ← Deps, entrypoint [prompt-pack]
├── .gitignore
├── .promptpackignore       ← Regras extra do utilizador (Phase 4)
├── README.md
└── plan.md                 ← Roadmap vivo, atualizado a cada etapa
```

---

## 3. Roadmap de Desenvolvimento

### Phase 0 — Foundation *(bloqueante para tudo)*

| Etapa | Descrição | Status |
|---|---|---|
| **0.1** | Criar estrutura de pastas + `pyproject.toml` + `.gitignore` + `plan.md` inicial | [x] |
| **0.2** | `git init` + `gh repo create Mendoncaa/MakePromptEasy --public` + push inicial | [x] |
| **0.3** | `pip install -e ".[dev]"` e validar que `prompt-pack --help` responde | [x] |

### Phase 1 — Core Engine *(etapas sequenciais, dependem de 0.3)*

| Etapa | Descrição | Status |
|---|---|---|
| **1.1** | `config.py` — `DEFAULT_IGNORE_DIRS`, `DEFAULT_IGNORE_EXTENSIONS`, `MAX_FILE_SIZE_BYTES` (500KB) | [x] |
| **1.2** | `filters.py` — `should_ignore(path: Path, config) -> bool` com lógica por extensão, nome de pasta e tamanho | [x] |
| **1.3** | `scanner.py` — `scan_directory(root: Path, config) -> Generator[Path, None, None]` — travessia recursiva lazy | [x] |
| **1.4** | `formatter.py` — `build_markdown(files, root: Path) -> str` — cabeçalho com meta, blocos ``` por ficheiro, rodapé com contagem | [x] |

### Phase 2 — CLI Layer *(depende de 1.4)*

| Etapa | Descrição | Status |
|---|---|---|
| **2.1** | `cli.py` — `prompt-pack <path> [--output FILE] [--no-clipboard] [--max-size KB]` com typer | [x] |
| **2.2** | Escrever `.md` em disco + `pyperclip.copy()` + painel `rich` com sumário (N ficheiros, N linhas, ~N tokens estimados) | [x] |

### Phase 3 — Tests *(paralelas entre si, dependem de 2.2)*

| Etapa | Descrição | Status |
|---|---|---|
| **3.1** | `test_filters.py` — testa cada regra de filtro individualmente com fixtures | [x] |
| **3.2** | `test_scanner.py` — cria árvore de ficheiros em `tmp_path`, valida generator | [x] |
| **3.3** | `test_formatter.py` — valida estrutura Markdown gerada (blocos, cabeçalhos) | [x] |
| **3.4** | Teste de integração end-to-end via `typer.testing.CliRunner` | [x] |

### Phase 4 — Polish *(depende de 3.4 passar a 100%)*

| Etapa | Descrição | Status |
|---|---|---|
| **4.1** | Suporte a `.promptpackignore` (estilo `.gitignore`, regras glob por linha) | [ ] |
| **4.2** | Estimativa de tokens no rodapé (regra simples: `chars / 4`) | [ ] |
| **4.3** | `README.md` completo com exemplos de uso + badge de testes | [ ] |

> **Regra de ouro:** Cada etapa só avança quando a anterior está **verde em testes, sem erros de linting (`ruff`), com commit+push feito** e `plan.md` atualizado.

---

## Verificação por Fase

1. **Phase 0** — `prompt-pack --help` imprime no terminal sem erro
2. **Phase 1** — `pytest tests/ -v` passa com 0 falhas nos unit tests do engine
3. **Phase 2** — Correr `prompt-pack ./src` gera `prompt_output.md` + mensagem de clipboard copiado
4. **Phase 3** — `pytest --cov=prompt_pack --cov-report=term-missing` mostra cobertura ≥ 90%
5. **Phase 4** — `.promptpackignore` com `*.log` exclui ficheiros `.log` corretamente

---

## Decisões e Exclusões

- **Excluído:** modo `--watch` está fora do escopo (one-shot cobre 99% dos casos de uso; watch mode seria Phase 5 futura)
- **Incluído:** binário `prompt-pack` instalável globalmente via `pipx install .`
- **Excluído:** interface gráfica, servidor web, integração direta com APIs de IA
