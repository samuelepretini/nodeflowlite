"""AbstractCommonNode: abstract base for LLM, tool-calling agent nodes.

Implements NodeInterface and provides the shared machinery, so a concrete agent
declares only its configuration (class variables):
- converts the declared ToolInterface tools into LangChain tools (schema derived
  from each tool's typed signature),
- builds the chat model (ChatOpenAI via OpenRouter),
- wires create_agent,
- invoke() template that runs the agent and produces the partial state update.

Concrete agents extend this class and set MODEL, SYSTEM_PROMPT and (optionally) TOOLS.

The framework OWNS the message emission. The agent never builds the `messages` channel
by hand and never returns it: it only shapes the OUTPUT through `on_result`, whose
RETURN VALUE becomes the node's message:
- `on_result(ctx, result) -> str | BaseMessage | None`
  - str        → wrapped as the node's message (AIMessage) and appended;
  - BaseMessage → emitted as-is (use it to control the type, e.g. a HumanMessage);
  - None        → no message emitted (suppress, e.g. a judge that only sets a verdict).
  Default: return the raw model message unchanged.
The sealed `reply()` calls `on_result` and turns its return into the partial; the agent
never touches `self._agent` or the raw channel, and there is no `reply` to remember to
return.

Side writes (NOT the message) go through `ctx.state`: `ctx.state.set_data(key, value)`
for the execution_data bag, `ctx.state.set(field, value)` for a declared field. The
agent may write them or not.

Input shaping stays in `build_prompt(state)` (SYNCHRONOUS, strings only): read
`state.last_message_content`, modify with `state.execution_data`, return the new string;
TRANSIENT (only what the model sees). For full control of the list override
`build_messages`; `ai_invoke(state)` is the ONLY place that awaits the model.
"""

from __future__ import annotations

import os
from abc import ABC
from typing import Any, ClassVar, Mapping

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from ..interface.NodeInterface import NodeInterface
from ..interface.StateInterface import StateInterface
from ..interface.ToolInterface import ToolInterface
from ..state.NodeContext import NodeContext
from ..state.State import State

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class AbstractCommonNode(NodeInterface, ABC):
    # Configuration: concrete agents override these class variables.
    MODEL: ClassVar[str]
    SYSTEM_PROMPT: ClassVar[str]
    TOOLS: ClassVar[list[type[ToolInterface]]] = []
    # Opt-in: set True to get ctx.previous (the previous State) pre-resolved — NO await,
    # usable in the SYNC on_result/build_prompt. One extra read per call only when set.
    LOAD_PREVIOUS: ClassVar[bool] = False

    def __init__(self) -> None:
        for required in ("MODEL", "SYSTEM_PROMPT"):
            if not getattr(self, required, None):
                raise TypeError(
                    f"{type(self).__name__} must define the class variable {required!r}"
                )
        tools = [self._to_langchain_tool(tool_cls()) for tool_cls in self.TOOLS]
        self._agent = create_agent(
            self._build_model(),
            tools=tools,
            system_prompt=self.SYSTEM_PROMPT,
        )

    @staticmethod
    def _to_langchain_tool(tool: ToolInterface) -> StructuredTool:
        # The argument schema is inferred from the tool's typed invoke() signature.
        return StructuredTool.from_function(
            coroutine=tool.invoke,
            name=tool.name,
            description=tool.description,
        )

    def _build_model(self) -> ChatOpenAI:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            # Explicit, actionable failure: this base needs an LLM, so a missing key
            # cannot be a vague downstream error. Raised at construction (build time),
            # which is exactly where the provider factory turns it into a clear report.
            raise RuntimeError(
                f"{type(self).__name__} needs an LLM but OPENROUTER_API_KEY is not set "
                "(put it in your project's .env)."
            )
        return ChatOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key, model=self.MODEL)

    async def invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # Sealed template: the base awaits the model, then `reply` turns on_result's return
        # into the messages partial. The node's side writes (ctx.state.set/set_data) are
        # collected separately by the builder, so we return only the message partial here.
        result = await self.ai_invoke(ctx.state)
        return self.reply(ctx, State(result))

    def reply(self, ctx: NodeContext, result: StateInterface) -> Mapping[str, Any]:
        # Framework-owned: call the agent's on_result and materialise its return into the
        # messages channel. The agent never builds {"messages": ...} by hand.
        return self._message_update(self.on_result(ctx, result))

    @staticmethod
    def _message_update(out: "str | BaseMessage | None") -> dict[str, Any]:
        if out is None:
            return {}  # suppress: this node emits no message
        if isinstance(out, BaseMessage):
            return {"messages": [out]}  # emitted as-is (caller controls the type)
        return {"messages": [AIMessage(content=out)]}  # str → the node's answer

    async def ai_invoke(self, state: StateInterface) -> Mapping[str, Any]:
        """Run the underlying LLM agent on the built messages; return its raw result.

        This is the only place that awaits the model. The messages sent to the model
        come from build_messages(state) (overridable), so the call site stays fixed.
        """
        return await self._agent.ainvoke({"messages": self.build_messages(state)})

    def on_result(
        self, ctx: NodeContext, result: StateInterface
    ) -> "str | BaseMessage | None":
        """Shape the node's OUTPUT from the (already resolved) model result.

        Synchronous — no async, no await. `result` is the model's output as a State (read
        result.last_message / result.last_message_content). RETURN the node's message:
        a str (wrapped as an AIMessage), a BaseMessage (emitted as-is, e.g. a HumanMessage),
        or None (emit nothing). Write side data via ctx.state.set_data / ctx.state.set and
        reach this thread's history via ctx.history. Default: return the raw model message.
        (`ctx` is a fresh per-call bundle — never stored on self.)
        """
        return result.last_message

    def build_prompt(self, state: StateInterface) -> str:
        """Shape the user prompt before the model sees it (SIMPLE input hook).

        The simplest thing an agent can do to the input: GET the text, modify it, RETURN
        it — strings only, no message plumbing. Typical body:

            text = state.last_message_content                     # get
            value = state.execution_data.get("key", "")           # a runtime variable
            return f"{text} ... {value}"                          # modify + return

        The returned string is put back into the messages by the base (no setter: the
        node instance is shared across requests, so nothing is stored on self). The
        change is TRANSIENT — only what the model sees, the persisted history stays
        raw. For a PERSISTED change use before_invoke (L2). Default: text unchanged.
        """
        return state.last_message_content

    def build_messages(self, state: StateInterface) -> list[BaseMessage]:
        """Build the full message list sent to the LLM (ADVANCED input hook).

        Plumbing owned by the base: it runs the text through build_prompt() and splices
        the result back, keeping the message type. Most agents override the simpler
        build_prompt() instead; override this only when you need full control of the list
        (add/reorder messages). The persisted history is never mutated.
        """
        history = state.messages
        if history and not isinstance(history[-1].content, str):
            return history  # non-text content (e.g. multimodal): leave it untouched
        original = state.last_message_content
        new_text = self.build_prompt(state)
        if new_text == original:
            return history
        if not history:
            return [HumanMessage(content=new_text)]
        enriched = history[-1].model_copy(update={"content": new_text})
        return [*history[:-1], enriched]
