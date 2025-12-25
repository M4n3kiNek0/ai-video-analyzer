"""
Simple optional API key guard.

If env AUTH_API_KEY is set, protected endpoints must send header `x-api-key`
matching that value. If the env is absent, the guard is a no-op.
"""
import os
from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)):
    expected = os.getenv("AUTH_API_KEY")
    if not expected:
        return True  # No protection configured
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return True

