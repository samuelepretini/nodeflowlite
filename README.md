# nodeflowlite

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-%E2%89%A5%203.11-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-early%20stage-orange.svg)](#status)

**A lightweight agentic framework built on LangGraph, where graphs are declared in YAML and behaviour lives in Python.**

It is a custom, self-hosted replacement for the licensed LangGraph Server: your graphs
run behind a plain FastAPI surface, with Postgres-backed state persistence — no managed
runtime required.

---

## The idea (the "why")

A framework user writes only **two things**:

1. their own **logic** — nodes (agents), routers, tools;
2. the **graph** — its topology, in a thin YAML file.

**Everything else is guaranteed by the framework, not delegated to you:** wiring,
`async`/`await`, error boundaries, the `messages` channel plumbing, concurrency safety,
schema derivation, state persistence. You should feel *protected* — the framework will
not let you fall into a technical pitfall (a forgotten `await`, an unsafe shared field,
a raw channel access).

The YAML stays "thin": it carries only the **topology** and expressive **names**. The
behaviour (model, prompt, tools, routing logic) stays in Python.

---

## Quickstart

> Requires Python ≥ 3.11 and an [OpenRouter](https://openrouter.ai/keys) API key
> (the LLM agents call models through OpenRouter). We use [`uv`](https://docs.astral.sh/uv/).

### Install

Early stage — install straight from git:

```bash
uv add "git+https://github.com/samuelepretini/nodeflowlite.git"
```

*(A PyPI release — `uv add nodeflowlite` — will follow once the API stabilises. The
importable package is currently `agent_platform`.)*

### Start a new project

Generate the project skeleton — the full tree (`agents/`, `routers/`, `tools/`,
`graphs/`) with stub nodes (one per level of the ladder), a runnable `MyGraph.yaml`,
a `PlatformManager.py`, and a `.env.example`:

```bash
# into a NEW folder (the project name defaults to the folder name)
uv run python -m agent_platform.scaffold ./my_project MyProject

# ...or into the CURRENT folder
uv run python -m agent_platform.scaffold .
```

It never overwrites existing files, so it is safe to re-run. The snippets below show
what the generated stubs look like and how to fill them.

### Write a tool

```python
# tools/Multiply.py
from agent_platform.core.interface.ToolInterface import ToolInterface

class Multiply(ToolInterface):
    name = "multiply"
    description = "Multiply two integers and return the product."

    async def invoke(self, a: int, b: int) -> int:   # the model-facing schema is
        return a * b                                  # derived from this signature
```

### Write an agent

The simplest agent declares only configuration — the framework owns the rest:

```python
# agents/WorkerAgent.py
from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from tools.Multiply import Multiply

class WorkerAgent(AbstractCommonNode):
    MODEL = "openai/gpt-4o"
    SYSTEM_PROMPT = "You are an assistant that answers using the available tools."
    TOOLS = [Multiply]
```

### Declare the graph (YAML)

```yaml
# graphs/WorkerGraph.yaml
name: WorkerGraph
description: A single worker that answers using the available tools.
version: 1

state:
  messages: { type: list, reducer: add_messages }

nodes:
  worker: { agent: WorkerAgent }

edges:
  - { from: START,  to: worker }
  - { from: worker, to: END }
```

### Run it

Your project's `PlatformManager` (the single initiator of the deployment) wires the
registry and serves the graphs over HTTP:

```bash
uv run python PlatformManager.py        # serves on http://localhost:8000
```

```bash
curl -s http://localhost:8000/graphs/WorkerGraph/invoke \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"demo","input":{"messages":[{"role":"user","content":"What is 6 times 7?"}]}}'
```

The response's `reply` is the answer, ready to use. Pass `"include_state": true` to also
get the full final state.

---

## Core concepts

### The ladder of control (how much the framework does for you)

Every node implements `NodeInterface` (`invoke(state) -> partial state update`). You pick
how much machinery to inherit:

| Level | Base | You write | Use it for |
|------|------|-----------|-----------|
| **L0** | `AbstractNode` (`run` + `data.add`), or `NodeInterface` directly | pure logic, no LLM | non-LLM nodes (counters, validation, I/O, ETL) |
| **L1** | `AbstractCommonNode` | only `MODEL` / `SYSTEM_PROMPT` / `TOOLS` | a standard tool-calling agent |
| **L2** | `AbstractHookedNode` | `before_invoke` / `after_invoke` / `on_error` hooks | input/output transforms, resilience |
| **L3** | `AbstractCommonNode` + sync `build_prompt` / `on_result` | shape the input prompt and/or the output | inject state vars (e.g. `execution_data`) into the prompt; custom result (e.g. a judge emitting `{verdict, attempts}`) |

The base owns the `await` (you never risk forgetting it). The state is an **object**
(`StateInterface`), not a raw dict: read it via `state.messages`, `state.last_message`,
`state.prompt`, `state.execution_data`, `state.get("field")`. To write output, the
framework hands you a fresh writable state (`ctx.state.set` / `ctx.state.set_data`) —
no dict to build, nothing to forget. Per-call data lives on per-call objects, never on
the node instance (nodes are shared across concurrent requests).

### Routers and loops

A router decides the next node: `RouterInterface.route(state) -> "nodeName" | "END"`. A
quality loop is just a cycle in the topology plus a router — e.g. `worker -> judge ->`
*(JudgeRouter)* `-> worker` (retry) `| END` (done).

### The registry

The YAML carries names; the registry resolves each name to a Python object (agents,
routers, state types, reducers). The basics (`str`, `int`, `add_messages`, …) ship
built-in, so you never re-declare them.

### Ports & Adapters

`core/` is framework-free (no FastAPI/DB imports). Adapters depend inward on core
interfaces, never the reverse: the HTTP surface lives in `connection/http`, persistence
in `persistence/`. Swapping the web framework or the database means rewriting only an
adapter.

### State persistence (checkpointer)

Each thread's state is checkpointed so a `thread_id` resumes a conversation and survives
a restart. The composition root picks the backend: set `DATABASE_URI` for Postgres,
otherwise an in-memory checkpointer is used (state lost on restart). A local Postgres is
provided via `docker compose up -d`.

```
GET /graphs/{name}/threads/{thread_id}/state   # read a thread's persisted state
```

---

## Framework vs. your project

- **`src/agent_platform/`** — the **framework**. You install it and do **not** edit it.
- **Your project** — a directory with `agents/`, `routers/`, `tools/`, `graphs/`, and a
  `PlatformManager.py` (the deployment's initiator). Your code is plugged into the
  framework via the registry. The framework never imports from your project — only the
  reverse.

The repo ships example user projects under `examples/` as runnable references
(`examples/assistant/` = a worker + a judge with a quality loop).

---

## Status

- **Phase A — done:** a linear graph runs end-to-end from YAML (loader → registry →
  builder → runtime), served over HTTP by a `PlatformManager`.
- **Phase B — done:** the judge loop (conditional edges, a judge agent + router) and
  state persistence (in-memory or Postgres, behind a port).
- **Next:** registry auto-discovery (no explicit name map), a scaffolding CLI, package
  rename to `nodeflowlite`, and a PyPI release.

---

## Documentation

More in-depth docs live under [`docs/`](./docs/):

- [**Installing a user project**](./docs/installing-a-user-project.md) — step-by-step from an empty folder to a running HTTP server.
- [**Operations manual**](./docs/operations-manual.md) — install, run a graph, read outputs, logging.
- [**Architecture**](./docs/architecture.md) — packages, ports & adapters, the ladder of control.
- [**Startup & execution**](./docs/startup-and-execution.md) — build-time vs per-request classes, with sequence diagrams.
- [**State history**](./docs/state-history.md) — reading a thread's historical state (`history` / `previous` / checkpoints).
- [**Architectural choices**](./docs/architectural-choices.md) — what the engine imposes vs what we chose.
- [**Dependency source (dev vs user)**](./docs/dependency-source-dev-vs-user.md) — editable install vs pinned copy.

---

## Contributing

Contributions are welcome and land through **maintainer-reviewed Pull Requests** — see
[`CONTRIBUTING.md`](CONTRIBUTING.md). Open an issue first for anything non-trivial.

---

## License

Licensed under the **[Apache License 2.0](LICENSE)** — free to use, modify, and
redistribute (including commercially), provided you retain the copyright and NOTICE and
state your changes. Contributions are accepted under the same license.

Copyright © 2026 Samuele Pretini.
