# Example: `assistant`

A self-contained **example user project** for `agent_platform`. It mirrors exactly what
a real user writes: their own logic (`agents/`, `routers/`, `tools/`) plus their graphs
(`graphs/*.yaml`) and a `PlatformManager.py` (the deployment's initiator). The framework
is used as a dependency — this folder never edits it.

> A real user keeps a project like this in **their own repo**, with `agent_platform`
> installed (`uv add agent-platform`). Here it lives inside the framework repo only to
> ship a runnable example. (`e2e_tests/` is separate: those are the framework's tests.)

## What it shows

- **WorkerGraph** — the minimal linear graph: `START → worker → END`.
- **AssistantGraph** — a quality loop: a worker answers, a judge validates and either
  loops back (with a critique) or stops at `END` (verdict OK, or max attempts).
- Agents along the **ladder of control**: `WorkerAgent` (L1, config-only),
  `ResilientWorkerAgent` (L2 hooks), `ManualWorkerAgent` / `JudgeAgent` (L3, custom
  output), `AttemptsCounterNode` (L0, non-LLM). Tools: `Multiply`, `GetWeather`.

## Run it

```bash
cp .env.example .env        # fill in OPENROUTER_API_KEY (+ optional DATABASE_URI)

# direct run (no server):
uv run python run_assistant_graph.py "What is 6 times 7? And the weather in Rome?"

# or serve over HTTP:
uv run python PlatformManager.py        # http://localhost:8000
```
