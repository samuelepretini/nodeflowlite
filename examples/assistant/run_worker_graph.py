"""Run this project's WorkerGraph end-to-end with a real LLM and a user prompt.

    uv run python run_worker_graph.py "what is 6 times 7?"

USER code: it uses the framework (agent_platform) but the framework does not depend
on it. Loads this project's graphs/WorkerGraph.yaml, builds it (loader -> registry ->
builder -> runtime) with the local WorkerAgent, sends the USER PROMPT as a message and
prints the answer. Runtime is used directly (level 3): no HTTP server needed.

The OpenRouter key is read from this project's `.env` (see .env.example). The
SYSTEM_PROMPT lives in the agent; the USER PROMPT travels at runtime in the state's
`messages` channel — that's what this script feeds in.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # this project's root: makes `agents`/`tools`/`routers` importable

from dotenv import load_dotenv

load_dotenv(HERE / ".env")  # this project's OpenRouter key

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from agent_platform.core.builder.GraphBuilder import GraphBuilder
from agent_platform.core.loader.YamlGraphLoader import YamlGraphLoader
from agent_platform.core.registry.StaticRegistry import StaticRegistry

from agents.WorkerAgent import WorkerAgent

GRAPH_FILE = HERE / "graphs" / "WorkerGraph.yaml"
DEFAULT_PROMPT = "Quanto fa 6 per 7? E che tempo fa a Roma?"


async def run_worker_graph(user_prompt: str, *, thread_id: str = "demo") -> str:
    """Build the WorkerGraph and run it with the given user prompt; return the answer."""
    dto = YamlGraphLoader().load(GRAPH_FILE)
    registry = StaticRegistry(agents={"WorkerAgent": WorkerAgent})
    runtime = GraphBuilder(registry, MemorySaver()).build(dto)

    final_state = await runtime.ainvoke(
        {"messages": [HumanMessage(content=user_prompt)]},  # <- the user prompt enters here
        thread_id=thread_id,
    )
    return final_state["messages"][-1].content


def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print(
            "Missing OPENROUTER_API_KEY. Put it in this project's .env "
            "(copy .env.example -> .env and fill it in), then re-run."
        )
        raise SystemExit(1)

    user_prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print(f"USER  > {user_prompt}")
    answer = asyncio.run(run_worker_graph(user_prompt))
    print(f"AGENT > {answer}")


if __name__ == "__main__":
    main()
