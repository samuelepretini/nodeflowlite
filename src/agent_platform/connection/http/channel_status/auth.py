"""Authentication: static token via the `Authorization: Bearer <token>` header.

If no token is configured (`settings.api_token is None`), auth is
disabled: convenient locally, to be avoided in production.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, Request, status


def verify_token(request: Request, authorization: str | None = Header(default=None)) -> None:
    token: str | None = request.app.state.settings.api_token
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
