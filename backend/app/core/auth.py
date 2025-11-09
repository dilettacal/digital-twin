"""Authentication helpers.

This module currently provides no-op authentication while we transition
from Clerk to Amazon Cognito. The functions are intentionally minimal so
we can plug Cognito verification in next without touching the rest of
the codebase.
"""
from typing import Optional

from fastapi import HTTPException, Request


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and validate user information from the request.

    Returns a user dict when authenticated, otherwise None.
    """
    # Authentication temporarily disabled.
    # TODO: integrate Amazon Cognito token validation here.
    _ = request  # suppress unused parameter warning until Cognito lands
    return None


async def require_auth(request: Request) -> dict:
    """
    Require authentication. Raises HTTPException if unauthenticated.
    """
    user = await get_current_user(request)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in.",
        )

    return user
