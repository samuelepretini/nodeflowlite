"""GraphBuilder: GraphDTO + registry -> compiled LangGraph graph (as a runtime).

It works entirely off the typed DTO (never the YAML text) and resolves every name
through the registry. Steps:
1. state schema: each StateFieldDTO -> a channel, with its reducer applied via
   Annotated[type, reducer] when declared;
2. nodes: each NodeDTO -> add_node(name, agent.invoke);
3. edges: each SimpleEdgeDTO -> add_edge (START/END mapped to the LangGraph
   sentinels); each ConditionalEdgeDTO -> add_conditional_edges(source,
   router.route, path_map) where the path_map turns each declared target name
   into the actual node (in particular "END" into the END sentinel).
4. compile (with the injected checkpointer) and wrap in LangGraphRuntime.

LangGraph lives here (and in the runtime): this is the engine adapter, the rest of
the system sees only GraphRuntimeInterface.
"""

from __future__ import annotations

from typing import Annotated, Any, Mapping, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from ..DTO.ConditionalEdgeDTO import ConditionalEdgeDTO
from ..DTO.GraphDTO import GraphDTO
from ..DTO.SimpleEdgeDTO import SimpleEdgeDTO
from ..DTO.StateFieldDTO import StateFieldDTO
from ..interface.GraphBuilderInterface import GraphBuilderInterface
from ..interface.GraphRuntimeInterface import GraphRuntimeInterface
from ..interface.NodeInterface import NodeInterface
from ..interface.RegistryInterface import RegistryInterface
from ..interface.RouterInterface import RouterInterface
from ..runtime.LangGraphRuntime import LangGraphRuntime
from ..state.NodeContext import NodeContext
from ..state.State import State
from ..state.WritableState import WritableState
from ..state.reducers import merge_dicts

_SENTINELS = {"START": START, "END": END}

# A free-form bag of runtime variables, auto-added to EVERY graph's state so nodes
# can stash/read data across the flow (and build_prompt can pull from it) without
# declaring static fields. Merged (not replaced) so partial writes accumulate.
EXECUTION_DATA_FIELD = "execution_data"


class GraphBuilder(GraphBuilderInterface):
    def __init__(self, registry: RegistryInterface, checkpointer: Any = None) -> None:
        self._registry = registry
        self._checkpointer = checkpointer

    def build(self, graph: GraphDTO) -> GraphRuntimeInterface:
        builder = StateGraph(self._build_state_schema(graph.state))

        # The compiled graph / runtime does not exist yet (nodes must be added BEFORE
        # compile), but each node needs a thread-bound StateHistory at call time. We hand
        # the node wrapper a mutable holder that the runtime fills in after compile; the
        # wrapper reads it lazily, only when a node actually runs (the runtime is set by
        # then). This keeps the history accessor flowing from the one place that owns the
        # compiled graph (the runtime), without leaking LangGraph into the nodes.
        runtime_holder: dict[str, GraphRuntimeInterface] = {}

        for node in graph.nodes:
            agent = self._registry.agent(node.agent)
            builder.add_node(node.name, self._as_node(agent, runtime_holder))

        for edge in graph.edges:
            if isinstance(edge, SimpleEdgeDTO):
                builder.add_edge(self._endpoint(edge.source), self._endpoint(edge.target))
            elif isinstance(edge, ConditionalEdgeDTO):
                router = self._registry.router(edge.router)
                builder.add_conditional_edges(
                    self._endpoint(edge.source),
                    self._as_router(router),
                    self._path_map(graph.name, edge),
                )
            else:  # pragma: no cover - guards against a new edge kind slipping through
                raise TypeError(f"{graph.name}: unknown edge type {type(edge).__name__}")

        compiled = builder.compile(checkpointer=self._checkpointer)
        runtime = LangGraphRuntime(compiled)
        runtime_holder["runtime"] = runtime
        return runtime

    def _build_state_schema(self, fields: tuple[StateFieldDTO, ...]) -> type:
        annotations: dict[str, Any] = {}
        for field in fields:
            py_type = self._registry.state_type(field.type)
            if field.reducer is not None:
                annotations[field.name] = Annotated[py_type, self._registry.reducer(field.reducer)]
            else:
                annotations[field.name] = py_type
        # Auto-inject the execution_data bag unless the user declared it explicitly
        # (then their declaration wins).
        if EXECUTION_DATA_FIELD not in annotations:
            annotations[EXECUTION_DATA_FIELD] = Annotated[dict, merge_dicts]
        return TypedDict("GraphState", annotations)

    def _path_map(self, graph_name: str, edge: ConditionalEdgeDTO) -> dict[str, Any]:
        # The router returns a target NAME (e.g. "worker" or "END"); the map turns each
        # name into the actual node — in particular "END" into LangGraph's END sentinel.
        if not edge.targets:
            raise ValueError(
                f"{graph_name}: conditional edge from {edge.source!r} via router "
                f"{edge.router!r} must declare `targets` (the reachable nodes)."
            )
        return {target: self._endpoint(target) for target in edge.targets}

    @staticmethod
    def _endpoint(name: str) -> str:
        return _SENTINELS.get(name, name)

    @staticmethod
    def _as_node(agent: NodeInterface, runtime_holder: Mapping[str, Any]):
        # Bridge LangGraph's dict-based node boundary to our object world: wrap the
        # state dict into a State so the node reads it via accessors. The node still
        # returns a partial-update dict, which LangGraph merges via the reducers.
        #
        # `config` is injected by LangGraph (it inspects this signature for a parameter
        # named `config`): it carries the thread_id, the only piece needed to bind the
        # thread's StateHistory. We resolve the history through the runtime (the owner of
        # the compiled graph) so LangGraph never leaks into the node.
        async def run(data: Mapping[str, Any], config: RunnableConfig) -> Mapping[str, Any]:
            thread_id = (config.get("configurable") or {}).get("thread_id", "")
            history = runtime_holder["runtime"].history(thread_id)
            # Opt-in pre-fetch: a node with LOAD_PREVIOUS=True gets ctx.previous resolved
            # (NO await) — usable even in the sync on_result/build_prompt.
            previous = await history.previous() if getattr(agent, "LOAD_PREVIOUS", False) else None
            state = WritableState(data)
            ctx = NodeContext(state=state, history=history, previous=previous)
            # The node's partial = what it staged on ctx.state (set/set_data) merged with
            # what invoke returns (the messages channel). Both flow to LangGraph's reducers.
            returned = await agent.invoke(ctx)
            return {**state.collect(), **(returned or {})}

        return run

    @staticmethod
    def _as_router(router: RouterInterface):
        def route(data: Mapping[str, Any]) -> str:
            return router.route(State(data))

        return route
