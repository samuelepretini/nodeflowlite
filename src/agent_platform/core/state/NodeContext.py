"""NodeContext: the per-call bundle handed to a node's logic (ctx).

The builder constructs ONE NodeContext per node call and passes it to invoke(ctx); the
abstract bases hand the same ctx to the node's extension point — uniformly ctx-first:
run(ctx) at L0, on_result(ctx, result) at L1/L3, before_invoke(ctx)/after_invoke(ctx,
result)/on_error(ctx, error) at L2. It carries everything the logic needs WITHOUT the
node reaching for plumbing or storing anything on the shared instance:

- state:    the running state as a WritableState — READ accessors (messages,
            last_message_content, execution_data, get) PLUS the node's writes
            (state.set(field, value), state.set_data(key, value)). Writes are staged and
            collected by the framework, not applied to the snapshot you read.
- history:  a read-only view of THIS thread's state history (previous / at / checkpoints
            / back), already bound to the current thread_id — the node calls
            ctx.history.previous() without ever knowing the thread_id (async, needs await).
- previous: the previous State, PRE-RESOLVED (no await) — present only when the node
            opts in with `LOAD_PREVIOUS = True`; None otherwise. Usable even in the SYNC
            extension points (on_result / build_prompt), where you cannot await.

The node's OUTPUT MESSAGE is not set through ctx: it is the return value of on_result
(str | BaseMessage | None), owned by the framework.

It is a per-call argument, never stored on self (the node instance is shared across
concurrent requests), so it is concurrency-safe by construction. Frozen: it is an
immutable handle to per-call collaborators, not a mutable state holder.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..interface.StateHistoryInterface import StateHistoryInterface
from ..interface.StateInterface import StateInterface
from ..interface.WritableStateInterface import WritableStateInterface


@dataclass(frozen=True)
class NodeContext:
    state: WritableStateInterface
    history: StateHistoryInterface
    previous: StateInterface | None = None
