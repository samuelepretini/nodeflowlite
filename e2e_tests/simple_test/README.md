# simple_test

A user project for `agent_platform`. You write the logic (`agents/`, `routers/`,
`tools/`) and the graph (`graphs/*.yaml`); the framework wires and serves them.

This project was scaffolded with stub agents — one per level of the ladder of
control — and a minimal runnable graph.

## Run it

```bash
cp .env.example .env          # fill in OPENROUTER_API_KEY (+ optional DATABASE_URI)
uv run python PlatformManager.py        # serves on http://localhost:8000
```

```bash
curl -s http://localhost:8000/graphs/MyGraph/invoke \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"demo","input":{"messages":[{"role":"user","content":"Hello"}]}}'
```

## The stub agents (ladder of control)

| File | Level | Base | You write |
|------|-------|------|-----------|
| `agents/CounterNode.py`   | L0 | `NodeInterface` directly      | pure `invoke()` logic (no LLM) |
| `agents/BasicWorker.py`   | L1 | `AbstractCommonNode`          | only MODEL / SYSTEM_PROMPT / TOOLS |
| `agents/HookedWorker.py`  | L2 | `AbstractHookedNode`          | before/after/on_error hooks |
| `agents/ShapingWorker.py` | L3 | `AbstractCommonNode` + `on_result` | shape the output |
| `agents/JudgeAgent.py`    | —  | `AbstractCommonNode` + `on_result` | a judge writing {verdict, attempts} |
| `routers/QualityRouter.py`| —  | `RouterInterface`             | `route(state) -> "node" \| "END"` |

Fill in a stub, register its name in `PlatformManager.py`, reference it in
`graphs/MyGraph.yaml`. To build a quality loop, uncomment the judge node/edges in
the YAML.
