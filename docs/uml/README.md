# UML documentation — agentic_platform

Diagrams of the framework design, to *see* the structure while designing it and for
onboarding. Source = **SVG** (versioned); the **PNG** is generated from the SVG
(downloadable/pasteable).

## Convention
- One file per diagram: `<area>-<what>.svg` (e.g. `ap14-statehistory-class-diagram.svg`).
- Notation (class diagram): «interface» / «abstract» / «class» / «DTO» in the boxes; **hollow-triangle** arrow = implements/extends (dashed = implements, solid = extends); **dashed open-head** arrow = calls/uses. **Dashed-border** box = boundary class (from another package), to dovetail the diagrams.
- Notation (sequence diagram): solid line + **filled head** = call; dashed line + **open head** = return/yield; vertical bars = activation; boxes = `loop`/`build` blocks.
- Color by *type* (interface / framework class / new / user node / external), with a legend in the diagram.

## Regenerate the PNG from an SVG
```
qlmanage -t -s 2400 -o . <file>.svg && mv <file>.svg.png <file>.png
# or, if installed: rsvg-convert -w 2400 <file>.svg -o <file>.png   |   cairosvg <file>.svg -o <file>.png -W 2400
```

## Index
- `ap14-statehistory-class-diagram.svg` — design of **AP-14** (StateHistory: state/checkpoint retrieval, injection via `NodeContext`).
- `config-class-diagram.svg` — the **config** package (empty/reserved): where configuration *actually* lives today (HttpSettings pydantic, env vars, checkpointer choice).
- `connection-class-diagram.svg` — the **connection** package (HTTP channel): `HttpTransport`/`HttpConnection` as adapters of `TransportInterface`/`ConnectionInterface`, the FastAPI router and the request/response DTOs.
- `core-class-diagram.svg` — the **core** package: the 15 ports (`core.interface`), the build pipeline (YAML → `GraphDTO` → `GraphBuilder` → `LangGraphRuntime`), the composition (Factory/Activator/`AbstractPlatformManager`) and the node/state block (detail in AP-14).
- `types-hierarchy-class-diagram.svg` — cross-cutting **type map**: each interface with its **concrete implementation** (*implements* arrows drawn in full) + the **abstract hierarchies** (the L0–L3 node ladder and the `AbstractPlatformManager` facade, *extends* arrows). Answers "who implements what".
- `node-ladder-class-diagram.svg` — the **L0–L3 node ladder by level**: one column per level, at the bottom the *user* node (e.g. `SheetReader`/`WorkerAgent`/`ResilientWorkerAgent`/`ManualWorkerAgent`), above it the whole chain up to `NodeInterface` (repeated per column). Clarifies that L2 extends L1 and that L3 = L1 with an override, not a class of its own.
- `activation-sequence-diagram.svg` — **sequence diagram** of startup: `run()` → `Activator.start()` → `Factory.open()` (opens the checkpointer; for each YAML: `Loader.load` → `GraphBuilder.build`) → provider ready → `Transport.serve()`. Clarifies who calls whom and the `YamlGraphLoader` ↔ `YamlGraphProviderFactory` relationship (ownership + delegation, not inheritance).
- `execution-sequence-diagram.svg` — **sequence diagram** of execution (framework already activated): a `POST /graphs/{name}/invoke` → `GraphExecutor.run` → `LangGraphRuntime.ainvoke` → LangGraph engine → (super-step loop) the `_as_node` wrapper that builds the `NodeContext` → the node's `invoke(ctx)` (ctx-first) → conditional router → `channel.send` → `InvokeResponse`. Generic graph; note on the node's L0–L3 levels.
- `persistence-class-diagram.svg` — the **persistence** package: the checkpointer adapters (`Memory`/`PostgresCheckpointerProvider`) behind `CheckpointerProviderInterface` (core), with the INTERNAL port `ConnectionPoolProviderInterface` for the psycopg pool. Nested lifecycles (Factory ⊃ checkpointer ⊃ pool).
- `scaffold-class-diagram.svg` — the **scaffold** package: the generator (`main` CLI → `ProjectScaffolder` → `project_templates` constants) that writes a user project's skeleton (agents L0–L3, routers, graphs, `PlatformManager.py`). Does not import the runtime, does not overwrite.
- `overview-architecture-diagram.svg` — **overview** (Ports & Adapters): the `core` (domain + ports) at the center, `connection` (HTTP, inbound) and `persistence` (checkpointer, outbound) implementing the ports, the user composition root + `scaffold`, the external engines. Includes the index of all the diagrams.

The three per-package diagrams share the **boundary classes** (dashed-border boxes) so
they can be dovetailed: e.g. `TransportInterface`/`ConnectionInterface` appear both in
*connection* and among the ports of *core*; `CheckpointerProviderInterface` ties *config*
and *core*.

> Overview still open (board **AP-16**): a synthesis diagram of the subsystems + a
> possible per-package one for `persistence` and `scaffold`.
