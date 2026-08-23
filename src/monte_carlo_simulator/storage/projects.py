"""Shared registers and simulation runs, attributed to their author.

The team asked for two things that turn out to be the same brick: picking up a
colleague's register rather than mailing spreadsheets around, and being able to
say who produced a reserve figure that went to a client.

So everything here is shared — every signed-in member sees every register and
every run — while authorship is recorded on write and never used to hide
anything. Deleting is deliberately absent for runs: a decision record that can
quietly disappear is not a decision record.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from monte_carlo_simulator.exceptions import ValidationError

MAX_NAME_LENGTH = 200


class ProjectError(ValidationError):
    """Raised when a register or run operation is rejected."""


@dataclass(frozen=True, slots=True)
class Author:
    """Who wrote something, kept readable even once the account is gone."""

    id: int | None
    full_name: str

    @classmethod
    def from_row(cls, user_id: int | None, full_name: str | None) -> Author:
        # A disabled or deleted account leaves its work behind: the foreign keys
        # are ON DELETE SET NULL precisely so history outlives the account.
        return cls(id=user_id, full_name=full_name or "Compte supprimé")


@dataclass(frozen=True, slots=True)
class StoredRegister:
    id: int
    name: str
    payload: dict[str, object]
    created_at: str
    updated_at: str
    created_by: Author
    updated_by: Author


@dataclass(frozen=True, slots=True)
class StoredRun:
    id: int
    register_id: int | None
    label: str
    config: dict[str, object]
    result: dict[str, object]
    created_at: str
    created_by: Author


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _clean_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ProjectError("Le nom est requis.")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ProjectError(f"Le nom ne peut pas dépasser {MAX_NAME_LENGTH} caractères.")
    return cleaned


def _decode(raw: str, field: str) -> dict[str, object]:
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - only a corrupted file
        raise ProjectError(f"Le champ « {field} » est illisible.") from exc
    if not isinstance(decoded, dict):  # pragma: no cover - same
        raise ProjectError(f"Le champ « {field} » n'est pas un objet.")
    return decoded


def _register_from_row(row: sqlite3.Row) -> StoredRegister:
    return StoredRegister(
        id=row["id"],
        name=row["name"],
        payload=_decode(row["payload"], "payload"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        created_by=Author.from_row(row["created_by"], row["created_by_name"]),
        updated_by=Author.from_row(row["updated_by"], row["updated_by_name"]),
    )


def _run_from_row(row: sqlite3.Row) -> StoredRun:
    return StoredRun(
        id=row["id"],
        register_id=row["register_id"],
        label=row["label"],
        config=_decode(row["config"], "config"),
        result=_decode(row["result"], "result"),
        created_at=row["created_at"],
        created_by=Author.from_row(row["created_by"], row["created_by_name"]),
    )


_REGISTER_SELECT = """
SELECT registers.*,
       creator.full_name AS created_by_name,
       editor.full_name  AS updated_by_name
FROM registers
LEFT JOIN users AS creator ON creator.id = registers.created_by
LEFT JOIN users AS editor  ON editor.id  = registers.updated_by
"""

_RUN_SELECT = """
SELECT runs.*, creator.full_name AS created_by_name
FROM runs
LEFT JOIN users AS creator ON creator.id = runs.created_by
"""


def save_register(
    connection: sqlite3.Connection,
    *,
    name: str,
    payload: dict[str, object],
    author_id: int,
    register_id: int | None = None,
) -> StoredRegister:
    """Create a register, or overwrite an existing one.

    An update records who touched it last without losing who created it, which
    is what makes shared editing traceable rather than anonymous.
    """
    label = _clean_name(name)
    encoded = json.dumps(payload, ensure_ascii=False)
    now = _now()

    if register_id is None:
        cursor = connection.execute(
            """
            INSERT INTO registers (name, payload, created_by, created_at, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (label, encoded, author_id, now, author_id, now),
        )
        new_id = cursor.lastrowid
        if new_id is None:  # pragma: no cover - the row was just inserted
            raise ProjectError("Le registre n'a pas pu être enregistré.")
        return _require_register(connection, new_id)

    if get_register(connection, register_id) is None:
        raise ProjectError("Ce registre est introuvable.")
    connection.execute(
        "UPDATE registers SET name = ?, payload = ?, updated_by = ?, updated_at = ? WHERE id = ?",
        (label, encoded, author_id, now, register_id),
    )
    return _require_register(connection, register_id)


def get_register(connection: sqlite3.Connection, register_id: int) -> StoredRegister | None:
    row = connection.execute(
        f"{_REGISTER_SELECT} WHERE registers.id = ?", (register_id,)
    ).fetchone()
    return _register_from_row(row) if row else None


def _require_register(connection: sqlite3.Connection, register_id: int) -> StoredRegister:
    stored = get_register(connection, register_id)
    if stored is None:  # pragma: no cover - callers just wrote the row
        raise ProjectError("Ce registre est introuvable.")
    return stored


def list_registers(connection: sqlite3.Connection) -> list[StoredRegister]:
    """Every register, most recently touched first — the team shares them all."""
    rows = connection.execute(f"{_REGISTER_SELECT} ORDER BY registers.updated_at DESC").fetchall()
    return [_register_from_row(row) for row in rows]


def delete_register(connection: sqlite3.Connection, register_id: int) -> None:
    """Remove a register, keeping the runs produced from it.

    The foreign key is ON DELETE SET NULL rather than CASCADE: tidying up an
    obsolete register must not erase the decisions taken from it.
    """
    if get_register(connection, register_id) is None:
        raise ProjectError("Ce registre est introuvable.")
    connection.execute("DELETE FROM registers WHERE id = ?", (register_id,))


def save_run(
    connection: sqlite3.Connection,
    *,
    label: str,
    config: dict[str, object],
    result: dict[str, object],
    author_id: int,
    register_id: int | None = None,
) -> StoredRun:
    """Record a completed simulation, with the assumptions it came from."""
    name = _clean_name(label)
    if register_id is not None and get_register(connection, register_id) is None:
        raise ProjectError("Ce registre est introuvable.")

    cursor = connection.execute(
        """
        INSERT INTO runs (register_id, label, config, result, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            register_id,
            name,
            json.dumps(config, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            author_id,
            _now(),
        ),
    )
    new_id = cursor.lastrowid
    if new_id is None:  # pragma: no cover - the row was just inserted
        raise ProjectError("L'exécution n'a pas pu être enregistrée.")
    stored = get_run(connection, new_id)
    if stored is None:  # pragma: no cover - same
        raise ProjectError("L'exécution n'a pas pu être relue.")
    return stored


def get_run(connection: sqlite3.Connection, run_id: int) -> StoredRun | None:
    row = connection.execute(f"{_RUN_SELECT} WHERE runs.id = ?", (run_id,)).fetchone()
    return _run_from_row(row) if row else None


def list_runs(
    connection: sqlite3.Connection, *, register_id: int | None = None, limit: int = 50
) -> list[StoredRun]:
    """Recent runs, newest first, optionally narrowed to one register."""
    if register_id is None:
        rows = connection.execute(
            f"{_RUN_SELECT} ORDER BY runs.created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = connection.execute(
            f"{_RUN_SELECT} WHERE runs.register_id = ? ORDER BY runs.created_at DESC LIMIT ?",
            (register_id, limit),
        ).fetchall()
    return [_run_from_row(row) for row in rows]
