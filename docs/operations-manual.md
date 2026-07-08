# Operations manual — agent_platform

Everything you need to **install** the framework and **use** it, in one place: create
the project, generate the skeleton, run a graph, read the outputs, and govern logging.

> Convention: the **framework** (`agent_platform`) is a dependency you install and do
> **not** modify; **your project** is a folder with `agents/`, `routers/`, `tools/`,
> `graphs/` and a `PlatformManager.py`. The framework never imports from your project,
> only the reverse.

Table of contents:
1. [Create the environment and install the libraries](#1-create-the-environment-and-install-the-libraries)
2. [Run a graph](#2-run-a-graph)
3. [Where to see the outputs](#3-where-to-see-the-outputs)
4. [Logging: using it and changing it](#4-logging-using-it-and-changing-it)
5. [Generate the project stub (empty ready-made classes)](#5-generate-the-project-stub-empty-ready-made-classes)

---

## 1. Create the environment and install the libraries

### Prerequisites
- **Python ≥ 3.11**
- **[uv](https://docs.astral.sh/uv/)** as project/dependency manager
- an **OpenRouter API key** (the LLM agents call the models via OpenRouter)
- *(optional)* a **Postgres** for state persistence; without it, an in-memory
  checkpointer is used (state lost on restart)

### Create the project and install the framework

```bash
mkdir my_project && cd my_project
uv init                      # creates pyproject.toml + .venv

# the framework, installed from git (early-stage; in the future: uv add nodeflowlite)
uv add "git+https://github.com/samuelepretini/nodeflowlite.git"

# your PlatformManager loads the .env: you need python-dotenv in YOUR project
uv add python-dotenv
```

### The full set of libraries

By installing `agent_platform` you get **transitively** all of its runtime
dependencies — you don't have to add them by hand:

| Library | What it is for |
|---|---|
| `fastapi` (≥0.115) | HTTP surface that exposes the graphs |
| `uvicorn[standard]` (≥0.30) | ASGI server that runs FastAPI |
| `pydantic` (≥2.7) | DTOs and validation |
| `pydantic-settings` (≥2.3) | configuration |
| `langgraph` (≥0.2) | graph execution engine + checkpointer |
| `langchain` / `langchain-core` (≥0.3) | message/tool abstractions |
| `langchain-openai` (≥0.2) | `ChatOpenAI` client (pointed at OpenRouter) |
| `pyyaml` (≥6.0) | YAML graph parsing |
| `langgraph-checkpoint-postgres` (≥3.1) | Postgres checkpointer |
| `psycopg[binary]` (≥3.3) · `psycopg-pool` (≥3.3) | Postgres driver and pool |

In **your** project you only add: `python-dotenv` (for `.env`). For framework
development, `pytest`, `httpx`, `python-dotenv` (the `dev` group) are also useful.

### The key (and persistence)

Create a `.env` at the project root:

```bash
# .env  (gitignored)
OPENROUTER_API_KEY=sk-or-v1-...
# DATABASE_URI=postgresql://agent:agent@localhost:5432/agent_platform   # optional
```

- without `DATABASE_URI` → **in-memory** checkpointer (handy locally, volatile state);
- with `DATABASE_URI` → **Postgres** checkpointer (persistent state, survives restart).

> You don't create the folder tree (`agents/`, `routers/`, …) by hand: the **scaffold**
> generates it — see [section 5](#5-generate-the-project-stub-empty-ready-made-classes).

---

## 2. Run a graph

### Start the server

Your project's `PlatformManager.py` is the **single initiator**: it wires the registry
and serves the graphs over HTTP.

```bash
uv run python PlatformManager.py        # → http://localhost:8000
```

The port is changed in the `PlatformManager`:
`build_transport()` → `HttpTransport(port=8000)` (default host `0.0.0.0`).

### Invoke a graph

`POST /graphs/{name}/invoke` with a JSON body:

```bash
curl -s http://localhost:8000/graphs/MyGraph/invoke \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"demo","input":{"messages":[{"role":"user","content":"Hi"}]}}'
```

Body fields (`InvokeRequest`):

| Field | Required | Meaning |
|---|---|---|
| `thread_id` | yes | identifies the thread → persistence/continuity of the conversation |
| `input` | yes | the graph input (shape depends on the graph; typical: `{messages:[…]}`) |
| `include_state` | no (default `false`) | if `true`, the response also includes the full **final state** |

Same `thread_id` → **resumes** that thread's previous state.

### All the endpoints

| Method & path | What it does |
|---|---|
| `GET /graphs` | lists the loaded graphs |
| `POST /graphs/{name}/invoke` | runs the graph (see above) |
| `GET /graphs/{name}/threads/{tid}/state` | thread's current persisted state (`values` + `next`) |
| `GET /graphs/{name}/threads/{tid}/state/previous` | state one step back (`back(1)`) |
| `GET /graphs/{name}/threads/{tid}/state/history?limit=N` | checkpoint index (id, node, step, timestamp) |
| `GET /graphs/{name}/threads/{tid}/state/at/{checkpoint_id}` | state at a specific checkpoint |

### Authentication

By default auth is **disabled** (handy locally). If a token is set in
`HttpSettings.api_token`, every route requires the `Authorization: Bearer <token>`
header (otherwise `401`). To enable it, pass the settings to the transport in the
`PlatformManager`:

```python
from agent_platform.connection.http.channel_operativity.HttpSettings import HttpSettings

def build_transport(self):
    return HttpTransport(port=8000, settings=HttpSettings(api_token="your-token"))
```

---

## 3. Where to see the outputs

There are **five** places, from the most immediate to the most detailed:

1. **The `invoke` response** (`InvokeResponse`):
   - `reply` → the content of the **last message** (the answer, ready to use);
   - `state` → the **full final state**, but only if you passed `"include_state": true`.

2. **The state endpoints** (section 2): the thread's **persisted** state, the previous
   state, the checkpoint list, and the state at a precise checkpoint.

3. **The `execution_data` bag**: whatever a node writes with
   `ctx.state.set_data("key", value)` ends up in `state.execution_data` → you read it
   via `include_state` or from the `state` endpoint.

4. **The checkpointer** (storage): each thread's state is saved at every super-step.
   In Postgres you can also inspect it directly on the DB; in-memory it lives in the process.

5. **The console logs** where the `PlatformManager` runs (see section 4): graph
   construction, HTTP requests, errors.

Example to get the full state in one shot:

```bash
curl -s http://localhost:8000/graphs/MyGraph/invoke \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"demo","input":{"messages":[{"role":"user","content":"Hi"}]},"include_state":true}'
```

---

## 4. Logging: using it and changing it

The framework uses Python's **standard `logging`**. It imposes no configuration: you
decide it in the `PlatformManager`.

### Who logs what

| Logger | Origin | Examples |
|---|---|---|
| `agent_platform.*` | the framework | `Built graph 'MyGraph' from MyGraph.yaml` (INFO), `Skipping graph …` (WARNING), build errors (ERROR) |
| `uvicorn`, `uvicorn.error` | the server | start/stop, errors |
| `uvicorn.access` | the server | one line per HTTP request |

### Change the level (global)

In the `PlatformManager` the stub sets:

```python
import logging
logging.basicConfig(level=logging.INFO)   # ← change to DEBUG / WARNING / ERROR
```

### Change the level per single logger

More surgical — raise the framework's detail and silence the access log:

```python
logging.getLogger("agent_platform").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)   # no line-per-request
```

### Format and destination

`basicConfig` accepts `format=` and `handlers=` (e.g. write to a file):

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler("platform.log"), logging.StreamHandler()],
)
```

### Logging from your own nodes

Use a per-module logger, no `print`:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("worker processed %s messages", n)
```

---

## 5. Generate the project stub (empty ready-made classes)

The **scaffold** writes the whole tree with commented stubs — an already-working
starting point, not finished logic.

### The command

```bash
# in a NEW folder (project name defaults to the folder name)
uv run python -m agent_platform.scaffold ./my_project MyProject

# ...or in the CURRENT folder
uv run python -m agent_platform.scaffold .
```

Form: `python -m agent_platform.scaffold [TARGET_DIR] [PROJECT_NAME]`. It **never
overwrites** existing files → it is safe to re-run on an already partially-filled folder
(it only prints what it added). Programmatic equivalent:
`ProjectScaffolder(target_dir, project_name).scaffold()`.

### The generated tree

```
my_project/
├── agents/
│   ├── __init__.py
│   ├── CounterNode.py      # L0 — pure-Python node, no LLM (AbstractNode)
│   ├── BasicWorker.py      # L1 — config-only agent (AbstractCommonNode)
│   ├── HookedWorker.py     # L2 — before/after/on_error hooks (AbstractHookedNode)
│   ├── ShapingWorker.py    # L3 — build_prompt / on_result (AbstractCommonNode)
│   └── JudgeAgent.py       # judge that writes {verdict, attempts}
├── routers/
│   ├── __init__.py
│   └── QualityRouter.py    # route(state) -> "node" | "END" (stop policy)
├── tools/
│   └── __init__.py
├── graphs/
│   └── MyGraph.yaml        # minimal runnable graph: START -> worker -> END
├── PlatformManager.py      # initiator: registry (YAML name -> class) + transport
├── .env.example            # copy to .env and set OPENROUTER_API_KEY
└── README.md
```

### The empty classes, by level of the "ladder of control"

| File | Level | Base | What you write |
|---|---|---|---|
| `agents/CounterNode.py` | L0 | `AbstractNode` (`run` + `data.add`) | pure logic, no LLM |
| `agents/BasicWorker.py` | L1 | `AbstractCommonNode` | only `MODEL` / `SYSTEM_PROMPT` / `TOOLS` |
| `agents/HookedWorker.py` | L2 | `AbstractHookedNode` | `before_invoke` / `after_invoke` / `on_error` hooks |
| `agents/ShapingWorker.py` | L3 | `AbstractCommonNode` + `build_prompt`/`on_result` | shape the input prompt and/or output |
| `agents/JudgeAgent.py` | — | `AbstractCommonNode` + `on_result` | a judge that writes `verdict`/`attempts` (via `ctx.state.set`) and returns the message (or `None`) |
| `routers/QualityRouter.py` | — | `RouterInterface` | `route(state) -> "node" \| "END"` |

### From stub to running graph (the workflow)

1. **fill in** a stub (e.g. `BasicWorker`: set `MODEL`, `SYSTEM_PROMPT`, `TOOLS`);
2. **register** its name in `PlatformManager.py` (`StaticRegistry` map: YAML name → class);
3. **reference** it in `graphs/MyGraph.yaml` (`nodes:` + `edges:`);
4. `cp .env.example .env`, set `OPENROUTER_API_KEY`;
5. `uv run python PlatformManager.py` and invoke (section 2).

For a **quality loop**, uncomment the `judge` node and the router edges in the YAML:
`worker -> judge -> (QualityRouter) -> worker (retry) | END (done)`.

---

### See also
- [`installing-a-user-project.md`](installing-a-user-project.md) — step-by-step install from an empty folder.
- [`startup-and-execution.md`](startup-and-execution.md) — build-time vs per-request classes, with sequence diagrams.
- [`architecture.md`](architecture.md) — packages, ports & adapters, ladder of control.
- [`state-history.md`](state-history.md) — the state history (`history` / `previous` / checkpoints).
