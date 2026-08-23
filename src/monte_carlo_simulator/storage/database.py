"""SQLite storage for the on-premises deployment.

The simulator is installed on one designated machine of the company network and
reached from a browser by every member, so the database is a single local file
rather than a service. SQLite is sized for that: a handful of concurrent users
on one host, no server to administer, one file to back up.

The file never lives inside the application bundle — a packaged executable
unpacks itself into a read-only temporary directory — so it is written to a
per-machine data directory instead, overridable with ``MCS_DATA_DIR``.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DATA_DIR_ENV = "MCS_DATA_DIR"
DATABASE_FILENAME = "monte_carlo.sqlite3"
APPLICATION_DIRNAME = "MonteCarloSimulator"

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    full_name     TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('admin', 'member')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TEXT    NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL,
    expires_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS registers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    payload     TEXT    NOT NULL,
    created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL,
    updated_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    register_id INTEGER REFERENCES registers(id) ON DELETE SET NULL,
    label       TEXT    NOT NULL,
    config      TEXT    NOT NULL,
    result      TEXT    NOT NULL,
    created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_registers_updated ON registers(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_register ON runs(register_id);
"""


def data_directory() -> Path:
    """Return the per-machine directory holding the database.

    ``MCS_DATA_DIR`` wins when set, which is how the test suite and a
    deliberately relocated installation point somewhere else.
    """
    override = os.environ.get(DATA_DIR_ENV, "").strip()
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    else:
        base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / APPLICATION_DIRNAME


def database_path() -> Path:
    return data_directory() / DATABASE_FILENAME


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open the database, creating the file and schema on first use."""
    target = path or database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target, isolation_level=None)
    connection.row_factory = sqlite3.Row
    # Foreign keys are off by default in SQLite and must be enabled per connection.
    connection.execute("PRAGMA foreign_keys = ON")
    # WAL lets readers work while one writer commits, which is what several
    # people browsing results during one save actually looks like.
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    _apply_schema(connection)
    return connection


def _apply_schema(connection: sqlite3.Connection) -> None:
    """Create anything missing and record the schema version.

    Every statement is ``IF NOT EXISTS``, so replaying the script on an older
    database is itself the migration — which holds only as long as versions stay
    purely additive. Renaming or dropping a column would need real migration
    steps here, and the recorded version is what would drive them.
    """
    connection.executescript(SCHEMA)
    row = connection.execute("SELECT version FROM schema_version").fetchone()
    if row is None:
        connection.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    elif row["version"] < SCHEMA_VERSION:
        connection.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))


@contextmanager
def session_scope(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a connection for one unit of work and always close it."""
    connection = connect(path)
    try:
        yield connection
    finally:
        connection.close()
