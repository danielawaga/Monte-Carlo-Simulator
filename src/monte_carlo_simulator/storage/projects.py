"""Saved registers and the local history of simulation runs.

Each desk keeps its own copy, so there is nobody to attribute anything to. What
remains — and what matters when a reserve figure leaves for a client — is a
dated record of every run with the assumptions it came from.

Deleting is deliberately absent for runs, and deleting a register detaches them
rather than erasing them: a decision record that can quietly disappear is not a
decision record.
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
class StoredRegister:
    id: int
    name: str
    payload: dict[str, object]
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class StoredRun:
    id: int
    register_id: int | None
    label: str
    config: dict[str, object]
    result: dict[str, object]
    created_at: str


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
    )


def _run_from_row(row: sqlite3.Row) -> StoredRun:
    return StoredRun(
        id=row["id"],
        register_id=row["register_id"],
        label=row["label"],
        config=_decode(row["config"], "config"),
        result=_decode(row["result"], "result"),
        created_at=row["created_at"],
    )


_REGISTER_SELECT = "SELECT * FROM registers"
_RUN_SELECT = "SELECT * FROM runs"


def save_register(
    connection: sqlite3.Connection,
    *,
    name: str,
    payload: dict[str, object],
    register_id: int | None = None,
) -> StoredRegister:
    """Create a register, or overwrite an existing one, keeping its creation date."""
    label = _clean_name(name)
    encoded = json.dumps(payload, ensure_ascii=False)
    now = _now()

    if register_id is None:
        cursor = connection.execute(
            """
            INSERT INTO registers (name, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (label, encoded, now, now),
        )
        new_id = cursor.lastrowid
        if new_id is None:  # pragma: no cover - the row was just inserted
            raise ProjectError("Le registre n'a pas pu être enregistré.")
        return _require_register(connection, new_id)

    if get_register(connection, register_id) is None:
        raise ProjectError("Ce registre est introuvable.")
    connection.execute(
        "UPDATE registers SET name = ?, payload = ?, updated_at = ? WHERE id = ?",
        (label, encoded, now, register_id),
    )
    return _require_register(connection, register_id)


def get_register(connection: sqlite3.Connection, register_id: int) -> StoredRegister | None:
    row = connection.execute(f"{_REGISTER_SELECT} WHERE id = ?", (register_id,)).fetchone()
    return _register_from_row(row) if row else None


def _require_register(connection: sqlite3.Connection, register_id: int) -> StoredRegister:
    stored = get_register(connection, register_id)
    if stored is None:  # pragma: no cover - callers just wrote the row
        raise ProjectError("Ce registre est introuvable.")
    return stored


def list_registers(connection: sqlite3.Connection) -> list[StoredRegister]:
    """Every saved register, most recently touched first."""
    rows = connection.execute(f"{_REGISTER_SELECT} ORDER BY updated_at DESC").fetchall()
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
    register_id: int | None = None,
) -> StoredRun:
    """Record a completed simulation, with the assumptions it came from."""
    name = _clean_name(label)
    if register_id is not None and get_register(connection, register_id) is None:
        raise ProjectError("Ce registre est introuvable.")

    cursor = connection.execute(
        """
        INSERT INTO runs (register_id, label, config, result, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            register_id,
            name,
            json.dumps(config, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
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
    row = connection.execute(f"{_RUN_SELECT} WHERE id = ?", (run_id,)).fetchone()
    return _run_from_row(row) if row else None


def list_runs(
    connection: sqlite3.Connection, *, register_id: int | None = None, limit: int = 50
) -> list[StoredRun]:
    """Recent runs, newest first, optionally narrowed to one register."""
    if register_id is None:
        rows = connection.execute(
            f"{_RUN_SELECT} ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = connection.execute(
            f"{_RUN_SELECT} WHERE register_id = ? ORDER BY created_at DESC LIMIT ?",
            (register_id, limit),
        ).fetchall()
    return [_run_from_row(row) for row in rows]
