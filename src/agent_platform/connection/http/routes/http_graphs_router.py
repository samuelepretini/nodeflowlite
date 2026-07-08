"""Graph routes: listing, synchronous invocation, reading a thread's state.

All protected by the token (router-level auth).

The `get_provider`/`get_runtime` functions are FastAPI dependencies (HTTP glue):
they pull the provider from the request and resolve the graph by name. They live here,
next to the routes that use them.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from agent_platform.core.runtime.GraphExecutor import GraphExecutor
from agent_platform.core.interface.GraphProviderInterface import GraphProviderInterface
from agent_platform.core.interface.GraphRuntimeInterface import GraphRuntimeInterface
from agent_platform.core.state.CheckpointNotFoundError import CheckpointNotFoundError

from ..channel_status.auth import verify_token
from ..channel_operativity.HttpConnection import HttpConnection
from ..DTO.GraphList import GraphList
from ..DTO.InvokeRequest import InvokeRequest
from ..DTO.InvokeResponse import InvokeResponse
from ..DTO.ThreadStateResponse import ThreadStateResponse
from ..DTO.HistoricalStateResponse import HistoricalStateResponse
from ..DTO.CheckpointResponse import CheckpointResponse
from ..DTO.CheckpointListResponse import CheckpointListResponse

router = APIRouter(prefix="/graphs", tags=["graphs"], dependencies=[Depends(verify_token)])


def get_provider(request: Request) -> GraphProviderInterface:
    """The provider is populated at startup by the lifespan and lives in `app.state.graphs`."""
    return request.app.state.graphs


def get_runtime(name: str, request: Request) -> GraphRuntimeInterface:
    """Resolves the graph `name`, or raises: 503 if it was declared but failed to
    build (with the reason), 404 if no such graph exists."""
    provider = get_provider(request)
    runtime = provider.get(name)
    if runtime is not None:
        return runtime
    reason = provider.failure(name)
    if reason is not None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Graph '{name}' failed to build: {reason}",
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Graph '{name}' not found")


@router.get("", response_model=GraphList)
async def list_graphs(provider: GraphProviderInterface = Depends(get_provider)) -> GraphList:
    return GraphList(graphs=provider.names())


@router.post("/{name}/invoke", response_model=InvokeResponse, response_model_exclude_none=True)
async def invoke(
    name: str,
    body: InvokeRequest,
    runtime: GraphRuntimeInterface = Depends(get_runtime),
) -> InvokeResponse:
    # IoC: channel + executor created PER-REQUEST, the tools injected as interfaces.
    channel = HttpConnection()
    executor = GraphExecutor(graph=runtime, channel=channel)
    await executor.run(body.input, thread_id=body.thread_id)
    state = channel.payload
    messages = state.get("messages") or []
    reply = getattr(messages[-1], "content", None) if messages else None
    return InvokeResponse(
        graph=name,
        thread_id=body.thread_id,
        reply=reply,
        state=state if body.include_state else None,
    )


@router.get("/{name}/threads/{thread_id}/state", response_model=ThreadStateResponse)
async def get_thread_state(
    name: str,
    thread_id: str,
    runtime: GraphRuntimeInterface = Depends(get_runtime),
) -> ThreadStateResponse:
    state = await runtime.get_state(thread_id=thread_id)
    return ThreadStateResponse(
        graph=name,
        thread_id=thread_id,
        values=dict(state.values),
        next=list(state.next),
    )


@router.get(
    "/{name}/threads/{thread_id}/state/previous",
    response_model=HistoricalStateResponse,
)
async def get_previous_state(
    name: str,
    thread_id: str,
    runtime: GraphRuntimeInterface = Depends(get_runtime),
) -> HistoricalStateResponse:
    # Read-only history view, bound to the thread at construction (no thread_id on methods).
    state = await runtime.history(thread_id).previous()
    return HistoricalStateResponse(
        graph=name,
        thread_id=thread_id,
        values=state.as_dict(),
    )


@router.get(
    "/{name}/threads/{thread_id}/state/history",
    response_model=CheckpointListResponse,
)
async def get_state_history(
    name: str,
    thread_id: str,
    limit: int | None = None,
    runtime: GraphRuntimeInterface = Depends(get_runtime),
) -> CheckpointListResponse:
    checkpoints = await runtime.history(thread_id).checkpoints(limit=limit)
    rows = [
        CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            node=checkpoint.node,
            step=checkpoint.step,
            created_at=checkpoint.created_at,
        )
        for checkpoint in checkpoints
    ]
    return CheckpointListResponse(graph=name, thread_id=thread_id, checkpoints=rows)


@router.get(
    "/{name}/threads/{thread_id}/state/at/{checkpoint_id}",
    response_model=HistoricalStateResponse,
)
async def get_state_at(
    name: str,
    thread_id: str,
    checkpoint_id: str,
    runtime: GraphRuntimeInterface = Depends(get_runtime),
) -> HistoricalStateResponse:
    try:
        state = await runtime.history(thread_id).at(checkpoint_id)
    except CheckpointNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found on thread '{thread_id}'",
        )
    return HistoricalStateResponse(
        graph=name,
        thread_id=thread_id,
        values=state.as_dict(),
        checkpoint_id=checkpoint_id,
    )
