#!/usr/bin/env python3
"""Bootstrap a fresh agent_platform project in THIS (empty) folder.

Copy this single file into an empty directory and run it with plain Python — it
needs NOTHING installed beyond `uv` (https://docs.astral.sh/uv/):

    python3 bootstrap.py

It does everything end-to-end:
  1. `uv init --bare`     -> turns the folder into a uv project (pyproject.toml + venv)
  2. `uv add <framework>` -> installs agent_platform into that venv
  3. scaffolds the stub   -> agents/, routers/, tools/, graphs/, PlatformManager.py, ...

Afterwards you only set your key and run the server:

    cp .env.example .env                 # fill in OPENROUTER_API_KEY
    uv run python PlatformManager.py     # http://localhost:8000

Where the framework comes from (the `uv add` source), in priority order:
  1. the first CLI argument:   python3 bootstrap.py /path/to/agentic_platform
  2. the AGENT_PLATFORM_SOURCE environment variable
  3. the DEFAULT_SOURCE constant below
A real user points this at the published package ("agent-platform") or the git URL,
e.g. "git+ssh://git@github.com/samuelepretini/AgenticPlatform.git".
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# CHOICE: default install source = a LOCAL path to the framework checkout, so the
# bootstrap works offline during development. Alternatives for a real install:
# "agent-platform" (PyPI) or the git URL. Override per-run via arg/env (see above).
DEFAULT_SOURCE = "git+https://github.com/samuelepretini/nodeflowlite.git"

HERE = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=HERE, check=True)


def resolve_source(argv: list[str]) -> str:
    if argv:
        return argv[0]
    return os.environ.get("AGENT_PLATFORM_SOURCE", DEFAULT_SOURCE)


def add_command(source: str) -> list[str]:
    # A local path source is almost always a dev checkout: install it --editable so
    # edits to the framework show up immediately, with no reinstall. A PyPI name or
    # git URL is a normal (copied) dependency.
    if Path(source).expanduser().is_dir():
        return ["uv", "add", "--editable", source]
    return ["uv", "add", source]


def main(argv: list[str]) -> int:
    if shutil.which("uv") is None:
        print("uv is not installed — see https://docs.astral.sh/uv/", file=sys.stderr)
        return 1
    source = resolve_source(argv)
    if not (HERE / "pyproject.toml").exists():
        run(["uv", "init", "--bare"])
    run(add_command(source))
    run(["uv", "run", "python", "-m", "agent_platform.scaffold", "."])
    print("\nDone. Next:")
    print("  cp .env.example .env                 # fill in OPENROUTER_API_KEY")
    print("  uv run python PlatformManager.py     # http://localhost:8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
