"""CLI entry point: scaffold a user project into a directory.

    python -m agent_platform.scaffold [TARGET_DIR] [PROJECT_NAME]

TARGET_DIR defaults to the current directory; PROJECT_NAME defaults to the
directory's name. Existing files are never overwritten. This is the engine behind
the bootstrap script and the planned `agent-platform new` command.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .ProjectScaffolder import ProjectScaffolder


def main(argv: list[str]) -> int:
    target = Path(argv[0]).resolve() if argv else Path.cwd()
    project_name = argv[1] if len(argv) > 1 else None
    created = ProjectScaffolder(target, project_name).scaffold()
    if not created:
        print("Nothing to do: every stub file already exists.")
        return 0
    print(f"Scaffolded {len(created)} file(s) into {target.name}/:")
    for path in created:
        print(f"  + {path.relative_to(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
