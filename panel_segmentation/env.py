"""Helpers for loading local environment variables from a repo .env file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def find_env_file(filename: str = ".env", start: Optional[os.PathLike[str] | str] = None) -> Optional[Path]:
    """Search upward from the current working directory for a .env file."""
    start_path = Path(start) if start is not None else Path.cwd()
    start_path = start_path.resolve()

    for candidate_dir in (start_path, *start_path.parents):
        candidate = candidate_dir / filename
        if candidate.is_file():
            return candidate

    return None


def load_env_file(
    path: Optional[os.PathLike[str] | str] = None,
    *,
    override: bool = False,
) -> Dict[str, str]:
    """Load KEY=VALUE pairs from a .env file into os.environ.

    The parser is intentionally small and supports the common forms used in
    local development:
    - blank lines
    - lines starting with '#'
    - optional 'export ' prefix
    - single-quoted or double-quoted values
    """
    env_path = Path(path) if path is not None else find_env_file()
    if env_path is None or not env_path.is_file():
        return {}

    loaded: Dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_wrapping_quotes(value.strip())
        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = value
        loaded[key] = value

    return loaded


def require_env(name: str) -> str:
    """Return an environment variable or raise a clear setup error."""
    value = os.environ.get(name)
    if value:
        return value
    raise RuntimeError(
        f"Missing required environment variable {name}. "
        f"Create a repo-root .env file or export {name} before running this notebook."
    )
