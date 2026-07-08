"""Run this project's AssistantGraph (worker + judge loop) end-to-end with a real LLM.

    uv run python e2e_tests/user1/run_assistant_graph.py "quanto fa 6 per 7?"

USER code: it uses the framework (agent_platform) but the framework does not depend
on it. Loads this project's graphs/AssistantGraph.yaml, builds it (loader -> registry
-> builder -> runtime) with the local WorkerAgent / JudgeAgent / JudgeRouter, sends
the USER PROMPT as a message and prints the answer plus the judge's verdict/attempts.

Unlike run_worker_graph.py, here the graph has a conditional edge: the judge loops
back to the worker until the answer is OK or MAX_ATTEMPTS is reached.

The OpenRouter key is read from this project's `.env` (see .env.example).
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

from agents.JudgeAgent import JudgeAgent
from agents.WorkerAgent import WorkerAgent
from routers.JudgeRouter import JudgeRouter

GRAPH_FILE = HERE / "graphs" / "AssistantGraph.yaml"
DEFAULT_PROMPT = "Quanto fa 6 per 7? E che tempo fa a Roma?"


async def run_assistant_graph(user_prompt: str, *, thread_id: str = "demo") -> dict:
    """Build the AssistantGraph and run it with the given user prompt; return the final state."""
    dto = YamlGraphLoader().load(GRAPH_FILE)
    registry = StaticRegistry(
        agents={"WorkerAgent": WorkerAgent, "JudgeAgent": JudgeAgent},
        routers={"JudgeRouter": JudgeRouter},
    )
    runtime = GraphBuilder(registry, MemorySaver()).build(dto)

    return await runtime.ainvoke(
        {"messages": [HumanMessage(content=user_prompt)]},  # <- the user prompt enters here
        thread_id=thread_id,
    )


def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print(
            "Missing OPENROUTER_API_KEY. Put it in this project's .env "
            "(copy .env.example -> .env and fill it in), then re-run."
        )
        raise SystemExit(1)

    user_prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print(f"USER   > {user_prompt}")
    final_state = asyncio.run(run_assistant_graph(user_prompt))
    print(f"AGENT  > {final_state['messages'][-1].content}")
    print(f"JUDGE  > verdict={final_state.get('verdict')!r} attempts={final_state.get('attempts')}")


if __name__ == "__main__":
    main()
