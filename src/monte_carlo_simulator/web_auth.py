"""Session-cookie authentication for the on-premises deployment.

The simulator now runs as one instance on a machine of the company network,
reached from a browser by every member, so identity is a real account rather
than a shared secret. Sessions live in the local database and travel in an
``httpOnly`` cookie: JavaScript cannot read the token, which is what keeps a
cross-site scripting bug from turning into stolen credentials.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response

from monte_carlo_simulator.storage import accounts, database

SESSION_COOKIE = "mcs_session"
SESSION_COOKIE_MAX_AGE = int(accounts.SESSION_LIFETIME.total_seconds())


def get_connection() -> Iterator[sqlite3.Connection]:
    """Provide one database connection per request."""
    connection = database.connect()
    try:
        yield connection
    finally:
        connection.close()


Connection = Annotated[sqlite3.Connection, Depends(get_connection)]
SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE)]


def issue_session_cookie(response: Response, token: str) -> None:
    """Attach a freshly opened session to the response.

    ``samesite="lax"`` is enough here: the interface is served from the same
    origin as the API, and it keeps a foreign page from silently posting to a
    logged-in session.
    """
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def optional_user(connection: Connection, session: SessionCookie = None) -> accounts.User | None:
    """Resolve the signed-in user, or ``None`` when nobody is signed in."""
    return accounts.user_for_session(connection, session or "")


OptionalUser = Annotated["accounts.User | None", Depends(optional_user)]


def current_user(user: OptionalUser) -> accounts.User:
    """Require a signed-in user, refusing the request otherwise."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentification requise.")
    return user


CurrentUser = Annotated[accounts.User, Depends(current_user)]


def current_admin(user: CurrentUser) -> accounts.User:
    """Require an administrator.

    A signed-in member gets 403 rather than 401: the request is authenticated,
    it is simply not allowed, and answering 401 would send the interface back to
    the sign-in screen for no reason.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=403, detail="Cette action est réservée aux administrateurs."
        )
    return user


CurrentAdmin = Annotated[accounts.User, Depends(current_admin)]
