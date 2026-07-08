# AP-14 — State history (read-only)

**Read-only** retrieval of a thread's historical `State`: reading the state of a past
super-step, jumping to a precise checkpoint, browsing the checkpoint index. Nothing
more: rollback/resume (modifying the history, restarting from a point) is AP-13, out of
scope.

The retrieved object is the **full `State`** — all user channels, `execution_data`
included — as it was at that super-step.

---

## 1. The contract: `StateHistoryInterface`

Methods, all `async`:

| Method | Returns | What it does |
|--------|---------|---------|
| `back(steps)` | `StateInterface` | the `State` `steps` super-steps back (`0` = your input, `1` = previous, …); raises `CheckpointNotFoundError` if the history is shorter |
| `previous()` | `StateInterface` | shortcut for `back(1)`, tolerant at the root (returns empty instead of raising) |
| `at(checkpoint_id)` | `StateInterface` | the `State` captured at that checkpoint (404 if it does not exist) |
| `checkpoints(limit=None)` | `list[StateCheckpoint]` | the lightweight checkpoint index, newest first |

The key point: the object **is bound to a single thread at construction time**. The
methods **do not** take a `thread_id` → per-thread isolation by construction. A node
cannot look into another thread; `at()` too is scoped to the bound thread, so a
`checkpoint_id` belonging to another thread is simply "not found"
(`CheckpointNotFoundError`), never a cross-thread leak.

`StateCheckpoint` is just the **index row** (the "menu"): identity and position,
without the state values.

```python
@dataclass(frozen=True)
class StateCheckpoint:
    checkpoint_id: str   # opaque checkpoint id
    node: str            # node that produced the checkpoint
    step: int            # super-step index
    created_at: str      # ISO-8601 timestamp
```

To read a row's values, you resolve it with `at(row.checkpoint_id)`.

---

## 2. Use FROM INSIDE A NODE (`ctx.history`)

Inside a node you have `ctx.history`, already bound to the current thread — you never
see a `thread_id`.

**Navigation: `back(n)` — how many steps back.** No indexes or ordering to remember:
`back(0)` is you (≈ `ctx.state`), `back(1)` is the previous state, `back(2)` two steps
back, etc. It is `async`, so `await` it from the **async** hooks (`run`, L2 hooks,
`invoke` override):

```python
async def run(self, ctx):
    prev = await ctx.history.back(1)     # the previous state
    two  = await ctx.history.back(2)     # two steps back
    # prev is the full State of that super-step (execution_data included)
```

**Without `await`: `ctx.previous`** (for the common case and for **sync** points).
Declare `LOAD_PREVIOUS = True` on the node: the framework pre-resolves the previous
state as an already-ready value — no `await`, usable **even in `on_result` /
`build_prompt`** (sync):

```python
class MyNode(AbstractNode):
    LOAD_PREVIOUS = True
    async def run(self, ctx):
        prev = ctx.previous            # no await — already resolved (None at the root)
```

For **specific** checkpoints there is still `at(checkpoint_id)`; for the menu,
`checkpoints()` (newest-first). In-node note: the rows of `checkpoints()` do not carry
the node label (`node=""`) — you navigate by `back(n)`/recency; the node name is only
available from outside (HTTP).

---

## 3. Use FROM OUTSIDE (HTTP)

All under token auth (router level):

| Endpoint | Maps to |
|----------|----------|
| `GET /graphs/{name}/threads/{tid}/state/previous` | `history(tid).previous()` |
| `GET /graphs/{name}/threads/{tid}/state/history?limit=` | `history(tid).checkpoints(limit)` |
| `GET /graphs/{name}/threads/{tid}/state/at/{checkpoint_id}` | `history(tid).at(checkpoint_id)` |

`at/{checkpoint_id}` responds **404** if the checkpoint does not exist on the thread
(`CheckpointNotFoundError` mapped to `HTTPException`).

---

## 4. Under the hood

The `LangGraphStateHistory` adapter isolates LangGraph behind the port and uses two
engine "ports" deliberately. For the **values** (`previous` / `at`) it reads the
**CHECKPOINTER** (the storage), not the compiled graph's `aget_state*`: this way it
works even **mid-run, from inside a node**, where the engine is empty due to reentrancy.
For the **index** (`checkpoints()`) it uses the **ENGINE** (`aget_state_history`),
because only it knows the node label (via the parent's `next`); when it returns empty —
again the in-node case — it **falls back** to the checkpointer, but there the node label
stays empty. LangGraph types never leave this module.

---

## 5. Choice B: the "ctx-first" extension point

Every node extension point receives a single per-call `NodeContext` (`ctx`) as its first
argument: `state` + `data` + `history`. The builder constructs it **once** per call and
passes it to `invoke(ctx)`; the abstract bases forward it to the user code.

```python
@dataclass(frozen=True)
class NodeContext:
    state: WritableStateInterface  # read+write state — accessors + set(field) / set_data(key)
    history: StateHistoryInterface # THIS thread's history (previous/at/checkpoints)
    previous: StateInterface | None = None  # opt-in with LOAD_PREVIOUS
```

Signatures per level:

| Level | Base | ctx-first signature(s) |
|---------|------|-------------------|
| L0 | `AbstractNode` | `run(ctx)` |
| L1 | `AbstractCommonNode` | `on_result(ctx, result)` |
| L2 | `AbstractHookedNode` | `before_invoke(ctx)` · `after_invoke(ctx, result)` · `on_error(ctx, error)` |
| L3 | `AbstractCommonNode` (override) | `on_result(ctx, result)` |
| — | direct `NodeInterface` | `invoke(ctx)` |

**Why B:**
- **A uniform signature that doesn't grow**: adding a new per-call collaborator (today
  `history`) means enriching `NodeContext`, not changing the signatures.
- **Concurrency-safe by construction**: `ctx` is a per-call argument, **never** put on
  `self` — the node instance is shared across concurrent requests.
- **The node doesn't touch the plumbing**: no `thread_id`, no direct engine access; it
  reads/writes `ctx.state` (`set`/`set_data`), navigates `ctx.history`.
