"""User accounts and browser sessions for the on-premises deployment.

Two roles only: ``admin`` manages accounts, ``member`` uses the simulator.
Everyone sees the same registers and results — the team asked for shared work
and traceability, not for per-person isolation — so authorship is recorded but
never used to hide anything from a colleague.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.storage.passwords import (
    hash_password,
    password_issue,
    verify_password,
)

Role = Literal["admin", "member"]

SESSION_LIFETIME = timedelta(hours=12)
SESSION_TOKEN_BYTES = 32


@dataclass(frozen=True, slots=True)
class User:
    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: str
    last_login_at: str | None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class AccountError(ValidationError):
    """Raised when an account operation is rejected."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
    )


def normalise_email(email: str) -> str:
    return email.strip().lower()


def has_any_user(connection: sqlite3.Connection) -> bool:
    """Tell whether the installation has been set up yet."""
    return connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None


def create_user(
    connection: sqlite3.Connection,
    *,
    email: str,
    full_name: str,
    password: str,
    role: Role = "member",
) -> User:
    address = normalise_email(email)
    if "@" not in address or address.startswith("@") or address.endswith("@"):
        raise AccountError("L'adresse e-mail est invalide.")
    if not full_name.strip():
        raise AccountError("Le nom complet est requis.")
    if role not in ("admin", "member"):
        raise AccountError("Le rôle doit être « admin » ou « member ».")
    issue = password_issue(password)
    if issue:
        raise AccountError(issue)

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (email, full_name, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (address, full_name.strip(), hash_password(password), role, _now()),
        )
    except sqlite3.IntegrityError as exc:
        raise AccountError("Un compte existe déjà pour cette adresse e-mail.") from exc

    created = get_user(connection, cursor.lastrowid) if cursor.lastrowid else None
    if created is None:  # pragma: no cover - the row was just inserted
        raise AccountError("Le compte n'a pas pu être relu après sa création.")
    return created


def create_first_admin(
    connection: sqlite3.Connection,
    *,
    email: str,
    full_name: str,
    password: str,
) -> User:
    """Create the founding administrator, only while no account exists.

    This is what makes a freshly installed executable usable without a command
    line. The window stays open only until the first account exists, so the
    administrator should be created right after the first launch.
    """
    if has_any_user(connection):
        raise AccountError("L'installation est déjà initialisée.")
    return create_user(
        connection, email=email, full_name=full_name, password=password, role="admin"
    )


def get_user(connection: sqlite3.Connection, user_id: int) -> User | None:
    row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_email(connection: sqlite3.Connection, email: str) -> User | None:
    row = connection.execute(
        "SELECT * FROM users WHERE email = ?", (normalise_email(email),)
    ).fetchone()
    return _row_to_user(row) if row else None


def list_users(connection: sqlite3.Connection) -> list[User]:
    rows = connection.execute("SELECT * FROM users ORDER BY full_name COLLATE NOCASE").fetchall()
    return [_row_to_user(row) for row in rows]


def count_active_admins(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM users WHERE role = 'admin' AND is_active = 1"
    ).fetchone()
    return int(row["total"])


def set_active(connection: sqlite3.Connection, user_id: int, *, active: bool) -> User:
    """Enable or disable an account, refusing to remove the last administrator."""
    user = get_user(connection, user_id)
    if user is None:
        raise AccountError("Ce compte est introuvable.")
    if not active and user.is_admin and user.is_active and count_active_admins(connection) <= 1:
        raise AccountError("Impossible de désactiver le dernier administrateur.")

    connection.execute("UPDATE users SET is_active = ? WHERE id = ?", (int(active), user_id))
    if not active:
        # A disabled account must lose its open browser sessions immediately.
        revoke_all_sessions(connection, user_id)
    refreshed = get_user(connection, user_id)
    assert refreshed is not None
    return refreshed


def set_role(connection: sqlite3.Connection, user_id: int, *, role: Role) -> User:
    if role not in ("admin", "member"):
        raise AccountError("Le rôle doit être « admin » ou « member ».")
    user = get_user(connection, user_id)
    if user is None:
        raise AccountError("Ce compte est introuvable.")
    if role == "member" and user.is_admin and count_active_admins(connection) <= 1:
        raise AccountError("Impossible de retirer le dernier administrateur.")

    connection.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    refreshed = get_user(connection, user_id)
    assert refreshed is not None
    return refreshed


def change_password(
    connection: sqlite3.Connection,
    user_id: int,
    *,
    new_password: str,
    revoke_other_sessions: bool = True,
) -> None:
    issue = password_issue(new_password)
    if issue:
        raise AccountError(issue)
    if get_user(connection, user_id) is None:
        raise AccountError("Ce compte est introuvable.")

    connection.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    if revoke_other_sessions:
        revoke_all_sessions(connection, user_id)


def authenticate(connection: sqlite3.Connection, *, email: str, password: str) -> User | None:
    """Return the matching active user, or ``None``.

    Callers get no clue whether the address or the password was wrong, and an
    unknown address still pays the hashing cost so that response time does not
    reveal which accounts exist.
    """
    row = connection.execute(
        "SELECT * FROM users WHERE email = ?", (normalise_email(email),)
    ).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    if not row["is_active"]:
        return None

    connection.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_now(), row["id"]))
    return _row_to_user(row)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def open_session(connection: sqlite3.Connection, user_id: int) -> str:
    """Create a browser session and return its token.

    Only the hash of the token is stored, so a stolen database copy cannot be
    replayed as a live session.
    """
    token = secrets.token_urlsafe(SESSION_TOKEN_BYTES)
    now = datetime.now(UTC)
    connection.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (
            _token_hash(token),
            user_id,
            now.isoformat(),
            (now + SESSION_LIFETIME).isoformat(),
        ),
    )
    return token


def user_for_session(connection: sqlite3.Connection, token: str) -> User | None:
    """Resolve a session token to its active user, dropping it once expired."""
    if not token:
        return None
    row = connection.execute(
        """
        SELECT sessions.expires_at, users.*
        FROM sessions JOIN users ON users.id = sessions.user_id
        WHERE sessions.token_hash = ?
        """,
        (_token_hash(token),),
    ).fetchone()
    if row is None:
        return None
    if datetime.fromisoformat(row["expires_at"]) <= datetime.now(UTC):
        close_session(connection, token)
        return None
    if not row["is_active"]:
        return None
    return _row_to_user(row)


def close_session(connection: sqlite3.Connection, token: str) -> None:
    connection.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


def revoke_all_sessions(connection: sqlite3.Connection, user_id: int) -> None:
    connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


def purge_expired_sessions(connection: sqlite3.Connection) -> int:
    cursor = connection.execute(
        "DELETE FROM sessions WHERE expires_at <= ?", (datetime.now(UTC).isoformat(),)
    )
    return cursor.rowcount


# Hashing this on import keeps the unknown-address path as costly as a real one.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
