# Architectural choices — inventory

Purpose: make the framework's design decisions **explicit**, separating what is
**imposed by the engine (LangGraph)** — hence not our margin — from what **we chose**
and remains debatable/changeable. It saves discovering them through trial and error,
and tells you what can be reworked.

> Terminology: the variables inside the state (`messages`, `execution_data`, `verdict`,
> `attempts`, …) we call **state attributes**. "Channel" is LangGraph's *internal* term
> (attribute + reducer): we use it only when talking about the engine internals.

---

## A. Imposed by LangGraph (NOT our margin)

Changing these would mean no longer using LangGraph as the engine.

| # | Choice | In brief |
|---|--------|----------|
| A1 | **State = a dict of attributes + reducers**, not a single mutable object | The engine keeps the state as data + merge functions; there is no "state object" that travels around. |
| A2 | **One state instance per node call** (a snapshot of the super-step) | The node receives the state *accumulated* at that step, not an object that lives for the whole execution. |
| A3 | **Writes are deltas merged by the reducers** between one super-step and the next | A node does not mutate the state in-place: it produces a delta, the engine merges it into the state of the next node. |
| A4 | **Per-attribute merge policy** | `messages` → append (`add_messages`); `execution_data` → dict merge; declared attribute → overwrite. |
| A5 | **Checkpoint per super-step** | Enables persistence, restart, and the AP-14 StateHistory. A direct consequence of A1–A3. |
| A6 | **Cap on super-steps per invocation** (`recursion_limit`) | LangGraph has a safety limit on loops (default 25). It exists; the *value* we pick is a B-thing (see B9). |

---

## B. Our choices (real margin — debatable)

Here there is design freedom: they can be reconsidered.

| # | Choice | Why / note | Where |
|---|--------|---------------|------|
| B1 | **OO `State` facade over the dict** | the user reads `state.messages` instead of indexing a dict | `core/state/State.py` |
| B2 | **`WritableState` (read+write) for nodes**; `State` read-only for routers/history | read and write on the same object; those who must not write don't see the setters | `core/state/WritableState.py` (AP-20) |
| B3 | **`ctx` (NodeContext) as the SINGLE per-call object** (state+history+previous) | a uniform signature that doesn't grow; never state on `self` (concurrency) | `core/state/NodeContext.py` |
| B4 | **`execution_data` auto-injected** as a bag attribute (merge) | a free place where nodes accumulate runtime variables without declaring them | `GraphBuilder` |
| B5 | **Message emission handled by the framework**: `on_result` RETURNS `str\|BaseMessage\|None` | no `reply` to remember; `None` = no message | `AbstractCommonNode` (AP-20) |
| B6 | **Node ladder L0–L3** (AbstractNode / AbstractCommonNode / AbstractHookedNode) | pick the minimum level of control you need | `core/abstract/` |
| B7 | **`before_invoke` = transient input-shaping** (via `with_input`) | shape *what the model sees* in this call, without touching the persisted history | `AbstractHookedNode` |
| B8 | **`last_message_content`** as an accessor to the last message's text | the name states the fact; the "prompt" role lives in `build_prompt` | AP-19 |
| B9 | **`recursion_limit = 1000`** | value chosen for long loops in a single invocation (alt: 1 item per invocation) | `LangGraphRuntime` |
| B10 | **Read-only StateHistory via the checkpointer, per-thread isolated** | retrieve historical states even from inside a node, without a `thread_id` | AP-14 |
| B11 | **Explicit name→class registry** in the PlatformManager | explicit map today; auto-discovery planned (**AP-9**) | `StaticRegistry` |
| B12 | **Ports & Adapters + IoC + strict naming** | framework-free core, adapters at the edges | skill `ioc-architecture-first` |

---

## How to reconsider a "B" choice

1. Is it in table B (our margin)? If it is in A, first verify whether LangGraph really imposes it.
2. Open/update a card on the **BOARD**; if it touches an **extension contract** (how nodes extend/implement), it is **discussed first** (rule in the `ioc-architecture-first` skill).
3. We agree on the new design, then implement it.

> This file is a living index: when a new non-obvious choice arises, it must be added here.
