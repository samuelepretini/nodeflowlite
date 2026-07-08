"""Public health check (no auth)."""

from __future__ import annotations

from fastapi import APIRouter

from ..DTO.HealthResponse import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/ok", response_model=HealthResponse)
async def ok() -> HealthResponse:
    return HealthResponse()
