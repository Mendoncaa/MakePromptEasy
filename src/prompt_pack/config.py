"""Configuration constants for prompt-pack."""

from __future__ import annotations

# Directories always ignored during scan
DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        ".eggs",
        "*.egg-info",
        ".tox",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".coverage",
        "htmlcov",
        ".idea",
        ".vscode",
        "__pypackages__",
        "site-packages",
        ".cache",
        "coverage",
        "tmp",
        "temp",
    }
)

# File extensions always ignored (binary, media, archives, etc.)
DEFAULT_IGNORE_EXTENSIONS: frozenset[str] = frozenset(
    {
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp",
        ".ico", ".svg", ".heic", ".raw",
        # Video / Audio
        ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".flac", ".ogg",
        # Archives
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
        # Compiled / binary
        ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin",
        ".class", ".jar", ".war", ".obj", ".o",
        # Documents / fonts / data
        ".pdf", ".docx", ".xlsx", ".pptx", ".odt",
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
        ".sqlite", ".db", ".mdb",
        # Misc
        ".DS_Store", ".lock",
        # Secrets / credentials
        ".pem", ".key", ".p12", ".pfx", ".jks", ".keystore",
    }
)

# Files ignored by exact name
DEFAULT_IGNORE_FILENAMES: frozenset[str] = frozenset(
    {
        ".DS_Store",
        "Thumbs.db",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        # Secrets / credentials / auth
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_ed25519",
        "credentials",
        "credentials.json",
        ".netrc",
        ".htpasswd",
    }
)

# Glob patterns for sensitive filenames (checked by fnmatch on name)
SENSITIVE_PATTERNS: tuple[str, ...] = (
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "id_ed25519*",
    "*.keystore",
)

# Maximum file size to include (bytes) — files above this are skipped
MAX_FILE_SIZE_BYTES: int = 500 * 1024  # 500 KB
