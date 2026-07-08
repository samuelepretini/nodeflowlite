# CHANGELOG / Build status — agentic_platform

Historical record of **what has been built**, phase by phase. Moved here from
`CLAUDE.md` to keep the latter lean: the record ("what happened") is not always-on
instruction. For the **how to write** a node/router/graph, see the
`agentic-platform-authoring` skill.

---

## Roadmap (YAML → compiled graph)

**DONE (base):** `core/DTO` graph model; Node/Router/Tool interfaces; node bases in
`core/abstract/` (L1 `AbstractCommonNode`, L2 `AbstractHookedNode`) + demos;
Multiply/GetWeather; LangChain/LangGraph dependencies.

### Phase A — DONE — a linear graph runs end-to-end from YAML (no router)

- `core/loader/YamlGraphLoader` (`GraphLoaderInterface`): `graphs/*.yaml` → `GraphDTO`
  (+ clear errors). Parses both simple AND conditional edges.
- `core/registry/StaticRegistry` (`RegistryInterface`): name → object
  (`agent`/`router`/`state_type`/`reducer`). Explicit maps from the composition root;
  ships the builtin types (str/int/.../) + reducers (add_messages) so the user does not
  re-declare them. Agents/routers instantiated lazily + cached. (Auto-discovery is a
  later swap behind the interface.)
- `core/builder/GraphBuilder` (`GraphBuilderInterface`): `GraphDTO` + registry →
  compiled `StateGraph`. Builds the state schema (`Annotated[type, reducer]`),
  `add_node(name, agent.invoke)`, `add_edge` (START/END mapped). **Conditional edges
  raised NotImplementedError (Phase B).**
- `core/runtime/LangGraphRuntime` (`GraphRuntimeInterface`): wraps the compiled graph;
  builds the `config` with `thread_id`. (Built by `GraphBuilder`, which stays in
  `core/builder/`.)
- `core/provider/YamlGraphProvider` + `YamlGraphProviderFactory` (`graphs_dir`,
  `registry`, `loader`): `open()` globs the dir, builds each graph (skips a broken one
  with a warning), returns the provider. Uses an in-memory `MemorySaver` checkpointer so
  thread/get_state work without Postgres.
- Composition root `e2e_tests/user1/PlatformManager.py` (extends
  `AbstractPlatformManager`): `build_factory()` wires `YamlGraphProviderFactory` +
  `StaticRegistry({"WorkerAgent": WorkerAgent})` over `e2e_tests/user1/graphs/`;
  `build_transport()` returns `HttpTransport(port=8000)`; the framework's `run()` does
  the lifecycle. Demo graph: `e2e_tests/user1/graphs/WorkerGraph.yaml`
  (`START → worker → END`). The dev echo stubs were removed once the real
  implementations arrived.

### Phase B — DONE — the judge loop + persistence

1. **DONE — JudgeAgent** (`e2e_tests/user1/agents/JudgeAgent.py`): L3, `TOOLS=[]`,
   gpt-4o-mini, judge prompt; sync `on_result` reads OK/KO from the judge's last message,
   increments `attempts`, and emits `{verdict, attempts}` — on OK it leaves `messages`
   intact (the final reply stays the worker's answer), on KO it appends the critique as a
   `HumanMessage` (verbatim, without a "KO:" prefix because the model text already starts
   with KO) so the worker improves on the next round. Max-attempts is NOT here (a routing
   concern). **Accepted behavior (by design):** on exit for max-attempts the last message
   is the judge's critique, so the final `reply` is that critique, not an answer — a
   graceful degradation ("I couldn't fully answer; here's what's missing"), deliberately
   NOT bypassed. Verified end-to-end with a real LLM: OK path → attempts=1 reply=worker's
   answer; no-answer/too-strict path → loop up to attempts=3 then END.
2. **DONE — JudgeRouter** (`e2e_tests/user1/routers/JudgeRouter.py`): RouterInterface,
   `MAX_ATTEMPTS=3`; `END` when verdict OK or attempts>=max, otherwise `worker`.
3. **DONE — builder: conditional edges** → `GraphBuilder.add_conditional_edges(source,
   router.route, path_map)` where `_path_map` turns each target name declared on the node
   (in particular `"END"`→END sentinel; raises if `targets` is empty).
   `AssistantGraph.yaml` (worker+judge loop) builds and runs; `answer`/`Answer` removed
   from its state (the worker is L1, no structured output for now — to be revisited as its
   own step). Run: `uv run python e2e_tests/user1/run_assistant_graph.py "..."`. The
   PlatformManager registers JudgeAgent + JudgeRouter.
4. **DONE — persistence** (`persistence/` adapter — psycopg/Postgres live ONLY here,
   never in the core): the checkpointer is injected into `YamlGraphProviderFactory` as
   `core/interface/CheckpointerProviderInterface` (port; an async-CM `open()` that returns
   a LangGraph `BaseCheckpointSaver`). Implementations:
   `persistence/checkpoint/MemoryCheckpointerProvider` (dev/test, wraps `MemorySaver`) and
   `persistence/checkpoint/PostgresCheckpointerProvider` (wraps `AsyncPostgresSaver`, calls
   `setup()`). The Postgres saver does NOT own its own connection: it receives a
   `persistence/db/ConnectionPoolProviderInterface` (a port kept INSIDE persistence — it
   names a psycopg type, so it cannot live in the core) implemented by
   `PostgresConnectionPoolProvider` (an `AsyncConnectionPool`, kwargs
   `autocommit=True, prepare_threshold=0`, opened via `async with`, `open=False`). The
   factory nests `checkpointer_provider.open()` inside its own `open()`. The **composition
   root** (`PlatformManager._build_checkpointer_provider`) picks the concrete: Postgres if
   `DATABASE_URI` is set, otherwise Memory (so the core does not import the adapter). Local
   Postgres via the root `docker-compose.yml` (`docker compose up -d`); `DATABASE_URI`
   documented in `e2e_tests/user1/.env.example`. Added dependencies:
   `langgraph-checkpoint-postgres`, `psycopg[binary]`, `psycopg-pool`. Verified with no DB
   (Memory path builds the graphs; Postgres path imports + builds without connecting).
   **Pending real e2e:** run with Postgres up and confirm the state survives a restart via
   `/graphs/{name}/threads/{tid}/state`.

### Planned refinement — registry auto-discovery (post-MVP, agreed)

Replace the explicit `StaticRegistry({"WorkerAgent": WorkerAgent, ...})` with a
`ScanningRegistry(packages=[...])` that imports the user's packages and indexes the
NodeInterface/RouterInterface classes by class name — so the user enumerates nothing
(they only write the class + the YAML). Same `RegistryInterface`, so
builder/factory/nodes stay untouched. Decision: keep it explicit for the MVP, move to
auto-discovery right after. (We deliberately keep ONE server serving N graphs — the
"LangGraph Server replacement" shape — not one process per graph.)
