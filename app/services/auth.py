"""Admin authentication service — credential verification and session checks."""

import os
import secrets
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse


def _get_admin_creds() -> tuple[str, str]:
    """Return (username, password) from env vars with defaults."""
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    return username, password


def verify_credentials(username: str, password: str) -> bool:
    """Check if the given credentials match the configured admin account."""
    admin_user, admin_pass = _get_admin_creds()
    # Constant-time-ish comparison to avoid timing leaks
    return secrets.compare_digest(username, admin_user) and secrets.compare_digest(
        password, admin_pass
    )


def is_authenticated(request: Request) -> bool:
    """Check whether the current request has a valid admin session."""
    return request.session.get("admin_authenticated", False)


def require_admin(request: Request) -> None:
    """FastAPI dependency: raise 401 if no valid admin session.

    HTML route handlers should catch this or check is_authenticated
    themselves and return a RedirectResponse for a better UX.
    """
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )


def require_admin_api(request: Request) -> None:
    """FastAPI dependency for API routes: raise 401 if no valid admin session.

    Used as a dependency on admin API routers to protect against
    unauthenticated access to CRUD endpoints.
    """
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Session"},
        )
