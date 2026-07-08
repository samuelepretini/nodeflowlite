# agentic_platform — Installing a user project

Every step to create **from scratch** a project that *uses* the framework: an empty
folder → a ready project → a running HTTP server. This is what a real user does (and
what you do to try the framework locally).

> **Key concept**: the user does not write the framework, they **install it as a
> dependency**. They only write *their* logic (`agents/`, `routers/`, `tools/`) and
> their graphs (`graphs/*.yaml`). The `bootstrap.py` script automates the whole setup.

---

## 0. Prerequisites

| Tool | Needed for | Check |
|---|---|---|
| **uv** | project/venv/dependency manager | `uv --version` |
| **Python ≥ 3.11** | runtime (usually managed by `uv`) | `python3 --version` |
| **OpenRouter key** | the LLM agents call the models via OpenRouter | from <https://openrouter.ai/keys> |

If `uv` is missing: see <https://docs.astral.sh/uv/> (one-line install).

---

## 1. Create an empty folder **outside** the framework repo

```bash
mkdir ~/agentic_test && cd ~/agentic_test
```

> ⚠️ **Outside the framework repo.** A user project is a standalone `uv` project: if
> you create it *inside* `agentic_platform/`, you nest a `uv` project inside another
> (conflicting `pyproject.toml`/`.venv`). Keep them separate.

---

## 2. Copy and run `bootstrap.py`

```bash
cp <path-to>/nodeflowlite/bootstrap.py .
python3 bootstrap.py
```

The script (which does **not** require the framework to be already installed — it uses
only the stdlib + `uv`) runs in sequence:

| Step | Internal command | Effect |
|---|---|---|
| 1 | `uv init --bare` | turns the folder into a `uv` project (`pyproject.toml` + `.venv`) |
| 2 | `uv add <framework>` | installs `agent_platform` into the project's `.venv` |
| 3 | `python -m agent_platform.scaffold .` | generates the project **stub** (see below) |

The created stub (13 files):

```
agents/   CounterNode.py  BasicWorker.py  HookedWorker.py  ShapingWorker.py  JudgeAgent.py
routers/  QualityRouter.py
tools/    (empty, ready for your tools)
graphs/   MyGraph.yaml          # minimal working graph: START -> worker -> END
PlatformManager.py             # composition root: registers agents/routers, picks the channel
.env.example                   # OPENROUTER_API_KEY (+ optional DATABASE_URI)
README.md
```

> **Where does `uv add` get the framework?** In order: 1st CLI argument → the
> `AGENT_PLATFORM_SOURCE` variable → the `DEFAULT_SOURCE` constant in the script. In
> development it is a **local path** (and the script installs it `--editable`); for a
> real user it will be PyPI (`nodeflowlite`) or a git URL. → see
> [`dependency-source-dev-vs-user.md`](./dependency-source-dev-vs-user.md).

---

## 3. Configure the key

```bash
cp .env.example .env
# then open .env and set the key:
#   OPENROUTER_API_KEY=sk-or-...
```

> `.env` is **gitignored**: it never lands in commits. It holds secrets.

`DATABASE_URI` is **optional**: if absent, thread state lives in RAM (lost on restart);
if present, the Postgres checkpointer is used.

---

## 4. Start the server

```bash
uv run python PlatformManager.py        # http://localhost:8000
```

At startup you should read:

```
INFO ... Built graph 'MyGraph' from MyGraph.yaml
INFO:     Uvicorn running on http://0.0.0.0:8000
```

`uv run` automatically activates the right `.venv` before launching the script: that is
why you don't have to "see" the library — `uv` finds it.

---

## 5. Try it with a request

In another terminal:

```bash
curl -s http://localhost:8000/graphs/MyGraph/invoke \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"demo","input":{"messages":[{"role":"user","content":"Hello"}]}}'
```

Expected response:

```json
{"graph":"MyGraph","thread_id":"demo","reply":"Hello! How can I assist you today?"}
```

Available endpoints:

| Method | Path | What it does |
|---|---|---|
| `GET`  | `/graphs` | lists the available graphs |
| `POST` | `/graphs/{name}/invoke` | runs the graph (pass `"include_state": true` for the full state) |
| `GET`  | `/graphs/{name}/threads/{thread_id}/state` | reads a thread's persisted state |

---

## 6. Write your own logic

The typical workflow:

1. create a tool in `tools/` or an agent in `agents/` (**one class per file**, file = class name);
2. register its **name** in the `StaticRegistry` inside `PlatformManager.py`;
3. reference that name in `graphs/MyGraph.yaml` (node/edge);
4. restart the server.

The generated stubs cover the levels of the **ladder of control** (`CounterNode` = L0
without LLM, `BasicWorker` = L1 config-only, `HookedWorker` = L2 hooks, `ShapingWorker`
= L3 custom output, `JudgeAgent` + `QualityRouter` = quality loop). See
[`architecture.md`](./architecture.md).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `404 "Graph 'MyGraph' not found"` | the graph **was not built** at startup (build failed) → typically a missing key | check the startup log: an `ERROR ... graph(s) FAILED to build ...` line gives the reason. Put the key in `.env` and restart |
| `503 "Graph '...' failed to build: ...OPENROUTER_API_KEY is not set"` | missing/empty key | set `OPENROUTER_API_KEY` in `.env`, restart |
| `address already in use` on `0.0.0.0:8000` | another server is already running on 8000 | stop the old one (Ctrl-C in its terminal) or change the port in `PlatformManager.build_transport()` |
| `command not found: python` | on your system it is `python3` | use `python3`, or always `uv run python ...` |
| I modify the framework but nothing changes | the framework is installed as a **copy** | reinstall, or use the **editable** install → see the dependency-source doc |
