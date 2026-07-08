"""Generates the stub of a fresh user project into a target directory.

This is a code GENERATOR: it writes user-facing files (`agents/`, `routers/`,
`tools/`, `graphs/`, `PlatformManager.py`, ...) — the same layout a real consumer
keeps in their own repo. It does not import or touch the framework runtime, and it
never overwrites existing files (re-runnable, safe on a partially-filled folder).

Usage (CLI) — generate an empty project skeleton:

    # into a NEW folder (project name defaults to the folder's name)
    uv run python -m agent_platform.scaffold ./my_project MyProject

    # ...or into the CURRENT folder
    uv run python -m agent_platform.scaffold .

Form: `python -m agent_platform.scaffold [TARGET_DIR] [PROJECT_NAME]` — TARGET_DIR
defaults to the current directory, PROJECT_NAME to its folder name. Next steps:
`cp .env.example .env`, add your key, `uv run python PlatformManager.py`.
Programmatic equivalent: `ProjectScaffolder(target_dir, project_name).scaffold()`.

It is the seed of the planned `agent-platform new <project>` CLI: the entrypoint a
user drops into an empty folder is a thin wrapper that calls `scaffold()`.
"""

from __future__ import annotations

from pathlib import Path

from .project_templates import (
    AGENTS_INIT,
    BASIC_WORKER,
    COUNTER_NODE,
    ENV_EXAMPLE,
    GRAPH_YAML,
    HOOKED_WORKER,
    JUDGE_AGENT,
    PLATFORM_MANAGER,
    PROJECT_NAME_PLACEHOLDER,
    QUALITY_ROUTER,
    README,
    ROUTERS_INIT,
    SHAPING_WORKER,
    TOOLS_INIT,
)


class ProjectScaffolder:
    def __init__(self, target_dir: Path, project_name: str | None = None) -> None:
        self._target_dir = target_dir
        # Default the project's name to the folder it lives in (e.g. "simple_test").
        self._project_name = project_name or target_dir.name

    def scaffold(self) -> list[Path]:
        """Write the stub, skipping any file that already exists. Returns the paths
        actually created (so the caller can report what was added vs left alone)."""
        created: list[Path] = []
        for relative_path, content in self._planned_files():
            path = self._target_dir / relative_path
            if self._write_if_absent(path, content):
                created.append(path)
        return created

    def _planned_files(self) -> list[tuple[str, str]]:
        return [
            ("agents/__init__.py", AGENTS_INIT),
            ("agents/CounterNode.py", COUNTER_NODE),
            ("agents/BasicWorker.py", BASIC_WORKER),
            ("agents/HookedWorker.py", HOOKED_WORKER),
            ("agents/ShapingWorker.py", SHAPING_WORKER),
            ("agents/JudgeAgent.py", JUDGE_AGENT),
            ("routers/__init__.py", ROUTERS_INIT),
            ("routers/QualityRouter.py", QUALITY_ROUTER),
            ("tools/__init__.py", TOOLS_INIT),
            ("graphs/MyGraph.yaml", self._render(GRAPH_YAML)),
            ("PlatformManager.py", self._render(PLATFORM_MANAGER)),
            (".env.example", ENV_EXAMPLE),
            ("README.md", self._render(README)),
        ]

    def _render(self, template: str) -> str:
        return template.replace(PROJECT_NAME_PLACEHOLDER, self._project_name)

    def _write_if_absent(self, path: Path, content: str) -> bool:
        if path.exists():
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
