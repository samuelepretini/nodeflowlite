"""Scaffold this folder into a fresh agent_platform user project.

Drop this file into an empty folder and run it once:

    uv run python init_project.py

It creates the stub (agents/, routers/, tools/, graphs/MyGraph.yaml,
PlatformManager.py, .env.example, README.md), skipping anything already present.
Then start writing your logic. The framework does the rest.
"""

from __future__ import annotations

from pathlib import Path

from agent_platform.scaffold.ProjectScaffolder import ProjectScaffolder

HERE = Path(__file__).resolve().parent


def main() -> None:
    created = ProjectScaffolder(HERE).scaffold()
    if not created:
        print("Nothing to do: every stub file already exists.")
        return
    print(f"Scaffolded {len(created)} file(s) into {HERE.name}/:")
    for path in created:
        print(f"  + {path.relative_to(HERE)}")
    print("\nNext: cp .env.example .env, then fill in agents/ and graphs/MyGraph.yaml.")


if __name__ == "__main__":
    main()
