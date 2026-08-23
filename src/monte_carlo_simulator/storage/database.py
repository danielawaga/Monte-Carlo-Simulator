"""SQLite storage for the per-desk installation.

Each desk runs its own copy, listening on the loopback interface only, so
nothing travels over the network and the database is simply a local file. That
file is what makes a saved register and a run history outlive the browser: the
interface used to keep drafts in ``localStorage``, which vanishes with the
browsing data and cannot be backed up.

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

SCHEMA_VERSION = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS registers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    payload    TEXT    NOT NULL,
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    register_id INTEGER REFERENCES registers(id) ON DELETE SET NULL,
    label       TEXT    NOT NULL,
    config      TEXT    NOT NULL,
    result      TEXT    NOT NULL,
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
    connection = sqlite3.connect(
        target,
        isolation_level=None,
        # FastAPI runs a synchronous dependency and its endpoint on different
        # threadpool threads, so the connection opened by the dependency is used
        # from another thread — sequentially, never concurrently, since it
        # belongs to a single request. SQLite's same-thread guard is too strict
        # for that pattern and would fail the request under any real load.
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    # Foreign keys are off by default in SQLite and must be enabled per connection.
    connection.execute("PRAGMA foreign_keys = ON")
    # WAL lets readers work while one writer commits, which is what several
    # people browsing results during one save actually looks like.
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    _apply_schema(connection)
    return connection


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _recorded_version(connection: sqlite3.Connection) -> int | None:
    if not _table_exists(connection, "schema_version"):
        return None
    row = connection.execute("SELECT version FROM schema_version").fetchone()
    return int(row["version"]) if row else None


_REBUILD_WITHOUT_ACCOUNTS = (
    "ALTER TABLE registers RENAME TO registers_v2",
    "ALTER TABLE runs RENAME TO runs_v2",
    """
    CREATE TABLE registers (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT    NOT NULL,
        payload    TEXT    NOT NULL,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE runs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        register_id INTEGER REFERENCES registers(id) ON DELETE SET NULL,
        label       TEXT    NOT NULL,
        config      TEXT    NOT NULL,
        result      TEXT    NOT NULL,
        created_at  TEXT    NOT NULL
    )
    """,
    """
    INSERT INTO registers (id, name, payload, created_at, updated_at)
        SELECT id, name, payload, created_at, updated_at FROM registers_v2
    """,
    """
    INSERT INTO runs (id, register_id, label, config, result, created_at)
        SELECT id, register_id, label, config, result, created_at FROM runs_v2
    """,
    "DROP TABLE registers_v2",
    "DROP TABLE runs_v2",
    "DROP TABLE IF EXISTS sessions",
    "DROP TABLE IF EXISTS users",
)


def _drop_accounts(connection: sqlite3.Connection) -> None:
    """Rebuild the tables an earlier version gave author columns.

    Version 2 belonged to a shared installation with user accounts; a per-desk
    copy has neither. ``CREATE TABLE IF NOT EXISTS`` leaves an existing table
    untouched, so the obsolete columns are dropped by rebuilding — and the
    registers already saved must survive it.
    """
    # Foreign keys are suspended for the rebuild: runs reference registers, and
    # renaming the parent mid-flight would otherwise break the constraint.
    connection.execute("PRAGMA foreign_keys = OFF")
    # Statements are issued one by one rather than through executescript, which
    # commits any pending transaction before running — the rebuild would then
    # not be atomic, and a failure halfway would leave the database in pieces.
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in _REBUILD_WITHOUT_ACCOUNTS:
            connection.execute(statement)
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
    connection.execute("PRAGMA foreign_keys = ON")


def _apply_schema(connection: sqlite3.Connection) -> None:
    """Create anything missing, migrate anything obsolete, record the version."""
    version = _recorded_version(connection)
    if version is not None and version < 3 and _table_exists(connection, "registers"):
        _drop_accounts(connection)

    connection.executescript(SCHEMA)
    if version is None:
        connection.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    elif version < SCHEMA_VERSION:
        connection.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))


@contextmanager
def session_scope(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a connection for one unit of work and always close it."""
    connection = connect(path)
    try:
        yield connection
    finally:
        connection.close()
