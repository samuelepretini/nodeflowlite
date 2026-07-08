"""Template contents for a fresh user project.

A scaffolded project mirrors the layout a real user keeps in their own repo:
`agents/`, `routers/`, `tools/`, `graphs/`, a `PlatformManager.py` (the deployment's
single initiator) and a `.env`. The framework (`agent_platform`) is a dependency;
these files live in the USER's project and the framework never imports them.

The agent/router files are STUBS: rich docstrings explaining each level of the
"ladder of control", plus a minimal method that just returns — a starting point to
fill in, not finished logic. `MyGraph.yaml` ships as a minimal runnable graph
(START -> worker -> END) so the project serves something out of the box.

These are plain strings; `ProjectScaffolder` writes them to disk. The only
substitution is the sentinel ``__PROJECT_NAME__`` (replaced via str.replace, not
str.format, so YAML/Python braces stay intact).
"""

from __future__ import annotations

PROJECT_NAME_PLACEHOLDER = "__PROJECT_NAME__"

AGENTS_INIT = "# Your agents go here — one class per file (file name = class name).\n"
ROUTERS_INIT = "# Your routers go here — one class per file (file name = class name).\n"
TOOLS_INIT = "# Your tools go here — one class per file (e.g. Multiply.py).\n"

# --- agents: one stub per level of the ladder of control ---------------------------

COUNTER_NODE = '''"""Stub node — level 0 (no LLM), via AbstractNode.

Pure-Python node for deterministic work: counters, validation, formatting, I/O, ETL
steps. No model, no tools. The framework hands run() a FRESH per-call NodeContext (ctx):
read from `ctx.state`, write with `ctx.state.set_data(key, value)`, reach this thread's
history via `ctx.history` — no dict to build, nothing to construct, concurrency-safe.

(To write the messages channel or a declared state field instead, implement
NodeInterface directly and return that partial update.)
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class CounterNode(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        # TODO your pure-Python logic: read with ctx.state.get(...) /
        # ctx.state.execution_data, write with ctx.state.set_data("key", value).
        count = ctx.state.execution_data.get("count", 0) + 1
        ctx.state.set_data("count", count)
'''

BASIC_WORKER = '''"""Stub agent — level 1 (config-only, AbstractCommonNode).

The standard tool-calling agent, and the level you will use most. You declare ONLY
configuration; the framework owns everything else — converting tools, building the
model, the awaited LLM call, and producing the partial state update.

Set MODEL, SYSTEM_PROMPT and (optionally) TOOLS (a list of ToolInterface classes
from tools/). There is no method body to write at this level.
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode


class BasicWorker(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: describe what this worker does."
    TOOLS = []                                    # TODO add tools, e.g. [Multiply]
'''

HOOKED_WORKER = '''"""Stub agent — level 2 (lifecycle hooks, AbstractHookedNode).

Same configuration as a level-1 worker, but you gain three hooks AROUND the LLM
call, each with a safe default (so override only the ones you need):
- before_invoke: validate/transform the INPUT; return ONLY the changed fields.
- after_invoke:  shape the OUTPUT; RETURN the node's message (str | BaseMessage | None).
- on_error:      fallback to keep the graph alive; default re-raises.

The sealed invoke() orchestrates: before -> LLM core -> after, guarded by on_error.
You never touch async plumbing beyond returning from these hooks.
"""

from __future__ import annotations

from typing import Any, Mapping

from langchain_core.messages import BaseMessage

from agent_platform.core.abstract.AbstractHookedNode import AbstractHookedNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class HookedWorker(AbstractHookedNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: describe what this worker does."
    TOOLS = []                                    # TODO add tools

    async def before_invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # TODO transform/validate the input. Return ONLY changed fields ({} = no change).
        return {}

    async def after_invoke(
        self, ctx: NodeContext, result: StateInterface
    ) -> "str | BaseMessage | None":
        # TODO shape the output: RETURN the node's message (str | BaseMessage | None).
        # Default: return the raw model message.
        return result.last_message

    async def on_error(
        self, ctx: NodeContext, error: Exception
    ) -> "str | BaseMessage | None":
        # TODO return a fallback message to survive the error. Default: re-raise.
        return await super().on_error(ctx, error)
'''

SHAPING_WORKER = '''"""Stub agent — level 3 (shape input/output, AbstractCommonNode).

The framework owns the LLM call and all the message plumbing. It offers two SIMPLE
SYNCHRONOUS hooks (strings/updates only — no list juggling):
- build_prompt(state): shape the INPUT — get the prompt, modify it with runtime
  variables, return it. TRANSIENT: it changes only what the model sees, the persisted
  history stays raw. (For a PERSISTED input change, use a HookedWorker's before_invoke.)
- on_result(ctx, result): shape the OUTPUT — build the node's partial update.

Override either or both. For full control of the message list override build_messages;
for full control of the orchestration override invoke() and call ai_invoke(state).
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class ShapingWorker(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: describe what this worker does."
    TOOLS = []                                    # TODO add tools

    def build_prompt(self, state: StateInterface) -> str:
        text = state.last_message_content                    # get
        # EXAMPLE: 'customer' is a sample execution_data key — use your own variables.
        customer = state.execution_data.get("customer", "")  # a runtime variable
        return f"{text}\\n\\nCustomer: {customer}"           # modify + return

    def on_result(self, ctx: NodeContext, result: StateInterface):
        # Shape the OUTPUT: RETURN the node's message — a str, a BaseMessage, or None
        # (suppress). Write side data via ctx.state.set_data / ctx.state.set. Default:
        # return the raw model message.
        return result.last_message
'''

JUDGE_AGENT = '''"""Stub agent — a judge that validates the worker and drives a quality loop.

A level-3 agent (AbstractCommonNode + on_result): the LLM produces a judgment, then
on_result writes the fields the router reads — `verdict` ("OK" / "KO...") and an
incremented `attempts`. On a KO it RETURNs its critique as a HumanMessage so the worker
sees it on the next loop.

Pair it with a router (QualityRouter) on a conditional edge:
    judge -> router -> worker (retry) | END (done)
The judge EVALUATES one answer; the router OWNS the stop policy (max attempts).
Keep those two responsibilities split.
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class JudgeAgent(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: reply 'OK' if the answer is complete, else 'KO' + a short critique."
    TOOLS = []

    def on_result(self, ctx: NodeContext, result: StateInterface):
        # TODO read the judgment (result.last_message_content) and set the verdict.
        # Stub: always approve so the loop terminates. Write fields via ctx.state.set;
        # RETURN None to emit no message (or a HumanMessage to feed a KO critique back).
        attempts = ctx.state.get("attempts", 0) + 1
        ctx.state.set("attempts", attempts)
        ctx.state.set("verdict", "OK")
        return None
'''

# --- routers ----------------------------------------------------------------------

QUALITY_ROUTER = '''"""Stub router — decides whether a quality loop continues or stops.

A router carries NO LLM and NO I/O: route(state) is a pure, synchronous decision
returning the next node's name, or "END" to finish the graph. It reads the state a
judge wrote (here `verdict` / `attempts`).

The stop POLICY lives here (e.g. MAX_ATTEMPTS), not in the judge: evaluating one
answer and deciding when to give up are different responsibilities.
"""

from __future__ import annotations

from typing import ClassVar

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class QualityRouter(RouterInterface):
    MAX_ATTEMPTS: ClassVar[int] = 3

    def route(self, state: StateInterface) -> str:
        # TODO decide from the state, e.g.:
        #   if state.get("verdict", "").startswith("OK") or state.get("attempts", 0) >= self.MAX_ATTEMPTS:
        #       return "END"
        #   return "worker"
        return "END"
'''

# --- graph, composition root, env, readme -----------------------------------------

GRAPH_YAML = """# __PROJECT_NAME__ graph — a minimal, runnable starting point.
#
# "Thin" YAML: only the graph TOPOLOGY lives here. Behaviour (model, prompt, tools)
# lives in your Python agents under agents/; the names are resolved by the registry
# you wire in PlatformManager.py. As shipped this runs START -> worker -> END using
# the BasicWorker stub (set OPENROUTER_API_KEY in .env first).

name: MyGraph
description: A single worker that answers the user.
version: 1

# Shared state flowing between nodes. `add_messages` is the built-in chat reducer.
state:
  messages: { type: list, reducer: add_messages }
  # verdict:  { type: str }              # uncomment for a judge / quality loop
  # attempts: { type: int, default: 0 }

# A node = an agent (the name is resolved by the registry in PlatformManager.py).
nodes:
  worker: { agent: BasicWorker }
  # judge:  { agent: JudgeAgent }        # uncomment to add a judge

# Edges wire the topology. Linear: { from: X, to: Y }. Conditional: a router picks.
edges:
  - { from: START,  to: worker }
  - { from: worker, to: END }
  # Quality loop — replace the "worker -> END" edge above with these:
  # - { from: worker, to: judge }
  # - from: judge
  #   router: QualityRouter              # route(state) -> "worker" | "END"
  #   targets: [worker, END]
"""

PLATFORM_MANAGER = '''"""__PROJECT_NAME__ PlatformManager: the single initiator of this deployment.

USER code. It declares only THIS project's info — which graphs/agents (the factory)
and which channel (the transport). The framework's AbstractPlatformManager owns the
startup/shutdown lifecycle; the framework (agent_platform) does not depend on this
folder, only the reverse.

    uv run python PlatformManager.py        (needs OPENROUTER_API_KEY in .env)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # makes this project's `agents`/`routers`/`tools` importable

from dotenv import load_dotenv

load_dotenv(HERE / ".env")  # this project's OpenRouter key (+ optional DATABASE_URI)

from agent_platform.connection.http.channel_operativity.HttpTransport import HttpTransport
from agent_platform.core.interface.CheckpointerProviderInterface import CheckpointerProviderInterface
from agent_platform.core.platform.AbstractPlatformManager import AbstractPlatformManager
from agent_platform.core.provider.YamlGraphProviderFactory import YamlGraphProviderFactory
from agent_platform.core.registry.StaticRegistry import StaticRegistry
from agent_platform.persistence.checkpoint.MemoryCheckpointerProvider import MemoryCheckpointerProvider
from agent_platform.persistence.checkpoint.PostgresCheckpointerProvider import PostgresCheckpointerProvider
from agent_platform.persistence.db.PostgresConnectionPoolProvider import PostgresConnectionPoolProvider

from agents.BasicWorker import BasicWorker
from agents.CounterNode import CounterNode
from agents.HookedWorker import HookedWorker
from agents.JudgeAgent import JudgeAgent
from agents.ShapingWorker import ShapingWorker
from routers.QualityRouter import QualityRouter

logging.basicConfig(level=logging.INFO)


class PlatformManager(AbstractPlatformManager):
    def build_factory(self) -> YamlGraphProviderFactory:
        # The registry maps the NAMES used in the YAML to your Python classes.
        # All stubs are registered; the shipped MyGraph.yaml only uses BasicWorker.
        registry = StaticRegistry(
            agents={
                "BasicWorker": BasicWorker,
                "HookedWorker": HookedWorker,
                "ShapingWorker": ShapingWorker,
                "CounterNode": CounterNode,
                "JudgeAgent": JudgeAgent,
            },
            routers={"QualityRouter": QualityRouter},
        )
        return YamlGraphProviderFactory(
            graphs_dir=HERE / "graphs",
            registry=registry,
            checkpointer_provider=self._build_checkpointer_provider(),
        )

    def _build_checkpointer_provider(self) -> CheckpointerProviderInterface:
        # Composition root: it alone knows the concretes. Postgres if a DATABASE_URI
        # is configured, otherwise an in-memory checkpointer (handy for local runs).
        db_uri = os.environ.get("DATABASE_URI")
        if db_uri:
            return PostgresCheckpointerProvider(PostgresConnectionPoolProvider(db_uri))
        logging.getLogger(__name__).info("No DATABASE_URI set: using in-memory checkpointer.")
        return MemoryCheckpointerProvider()

    def build_transport(self) -> HttpTransport:
        # The HTTP channel: serves the graphs over FastAPI on this port.
        return HttpTransport(port=8000)


if __name__ == "__main__":
    asyncio.run(PlatformManager().run())
'''

ENV_EXAMPLE = """# Copy this file to `.env` and fill in your key. `.env` is gitignored.

# OpenRouter API key used by the LLM agents (https://openrouter.ai/keys)
OPENROUTER_API_KEY=

# Postgres checkpointer (OPTIONAL). If unset, an in-memory checkpointer is used
# (state lost on restart).
# DATABASE_URI=postgresql://agent:agent@localhost:5432/agent_platform
"""

README = """# __PROJECT_NAME__

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
curl -s http://localhost:8000/graphs/MyGraph/invoke \\
  -H "Content-Type: application/json" \\
  -d '{"thread_id":"demo","input":{"messages":[{"role":"user","content":"Hello"}]}}'
```

## The stub agents (ladder of control)

| File | Level | Base | You write |
|------|-------|------|-----------|
| `agents/CounterNode.py`   | L0 | `AbstractNode` (`run` + `data.add`) | pure logic, no LLM |
| `agents/BasicWorker.py`   | L1 | `AbstractCommonNode`          | only MODEL / SYSTEM_PROMPT / TOOLS |
| `agents/HookedWorker.py`  | L2 | `AbstractHookedNode`          | before/after/on_error hooks |
| `agents/ShapingWorker.py` | L3 | `AbstractCommonNode` + `build_prompt`/`on_result` | shape input prompt and/or output |
| `agents/JudgeAgent.py`    | —  | `AbstractCommonNode` + `on_result` | a judge writing {verdict, attempts} |
| `routers/QualityRouter.py`| —  | `RouterInterface`             | `route(state) -> "node" \\| "END"` |

Fill in a stub, register its name in `PlatformManager.py`, reference it in
`graphs/MyGraph.yaml`. To build a quality loop, uncomment the judge node/edges in
the YAML.
"""
