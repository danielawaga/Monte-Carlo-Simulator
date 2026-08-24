"""Tests for saved registers and the local run history."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from monte_carlo_simulator.storage import database, projects
from monte_carlo_simulator.storage.projects import ProjectError

PAYLOAD: dict[str, object] = {
    "schemaVersion": "1.0",
    "metadata": {"projectName": "Extension usine", "defaultUnit": "EUR"},
    "items": [{"id": "risk-1", "name": "Études", "distribution": "triangular"}],
}
CONFIG: dict[str, object] = {"simulations": 10_000, "seed": 42}
RESULT: dict[str, object] = {"summary": {"mean": 1234.5}, "percentiles": [{"P80": 1500}]}


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    handle = database.connect(tmp_path / "projects.sqlite3")
    try:
        yield handle
    finally:
        handle.close()


class TestRegisters:
    def test_saving_keeps_the_payload_intact(self, connection: sqlite3.Connection) -> None:
        stored = projects.save_register(connection, name="Extension usine", payload=PAYLOAD)

        assert stored.name == "Extension usine"
        assert stored.payload == PAYLOAD
        assert stored.created_at and stored.updated_at

    def test_overwriting_keeps_the_original_creation_date(
        self, connection: sqlite3.Connection
    ) -> None:
        original = projects.save_register(connection, name="Extension usine", payload=PAYLOAD)

        edited = projects.save_register(
            connection,
            name="Extension usine — révisé",
            payload={**PAYLOAD, "items": []},
            register_id=original.id,
        )

        assert edited.id == original.id
        assert edited.name == "Extension usine — révisé"
        assert edited.payload["items"] == []
        assert edited.created_at == original.created_at, "la date de création ne doit pas bouger"

    def test_every_saved_register_is_listed(self, connection: sqlite3.Connection) -> None:
        projects.save_register(connection, name="Projet A", payload=PAYLOAD)
        projects.save_register(connection, name="Projet B", payload=PAYLOAD)

        listing = projects.list_registers(connection)

        assert {register.name for register in listing} == {"Projet A", "Projet B"}

    @pytest.mark.parametrize("name", ["", "   ", "x" * (projects.MAX_NAME_LENGTH + 1)])
    def test_an_unusable_name_is_refused(self, connection: sqlite3.Connection, name: str) -> None:
        with pytest.raises(ProjectError):
            projects.save_register(connection, name=name, payload=PAYLOAD)

    def test_updating_an_unknown_register_is_refused(self, connection: sqlite3.Connection) -> None:
        with pytest.raises(ProjectError, match="introuvable"):
            projects.save_register(connection, name="Fantôme", payload=PAYLOAD, register_id=999)

    def test_an_accented_payload_survives_the_round_trip(
        self, connection: sqlite3.Connection
    ) -> None:
        payload = {"metadata": {"projectName": "Réhabilitation à Ouagadougou — phase 2"}}

        stored = projects.save_register(connection, name="Accents", payload=payload)

        assert projects.get_register(connection, stored.id).payload == payload


class TestRuns:
    def test_a_run_records_the_assumptions_it_came_from(
        self, connection: sqlite3.Connection
    ) -> None:
        """What makes a figure sent to a client traceable back to its inputs."""
        register = projects.save_register(connection, name="Extension usine", payload=PAYLOAD)

        run = projects.save_run(
            connection, label="Référence", config=CONFIG, result=RESULT, register_id=register.id
        )

        assert run.config == CONFIG
        assert run.result == RESULT
        assert run.register_id == register.id

    def test_runs_can_be_narrowed_to_one_register(self, connection: sqlite3.Connection) -> None:
        first = projects.save_register(connection, name="A", payload=PAYLOAD)
        second = projects.save_register(connection, name="B", payload=PAYLOAD)
        projects.save_run(
            connection, label="Run A", config=CONFIG, result=RESULT, register_id=first.id
        )
        projects.save_run(
            connection, label="Run B", config=CONFIG, result=RESULT, register_id=second.id
        )

        assert [run.label for run in projects.list_runs(connection, register_id=first.id)] == [
            "Run A"
        ]
        assert len(projects.list_runs(connection)) == 2

    def test_a_run_attached_to_an_unknown_register_is_refused(
        self, connection: sqlite3.Connection
    ) -> None:
        with pytest.raises(ProjectError, match="introuvable"):
            projects.save_run(
                connection, label="Orphelin", config=CONFIG, result=RESULT, register_id=999
            )


class TestHistorySurvives:
    def test_deleting_a_register_keeps_the_runs_it_produced(
        self, connection: sqlite3.Connection
    ) -> None:
        """A decision record must not vanish when its source is tidied away."""
        register = projects.save_register(connection, name="Obsolète", payload=PAYLOAD)
        run = projects.save_run(
            connection, label="Décision P80", config=CONFIG, result=RESULT, register_id=register.id
        )

        projects.delete_register(connection, register.id)

        survivor = projects.get_run(connection, run.id)
        assert survivor is not None
        assert survivor.label == "Décision P80"
        assert survivor.register_id is None, "le lien est coupé, pas l'exécution"
        assert survivor.config == CONFIG, "les hypothèses du run restent lisibles"

    def test_deleting_an_unknown_register_is_refused(self, connection: sqlite3.Connection) -> None:
        with pytest.raises(ProjectError, match="introuvable"):
            projects.delete_register(connection, 999)


class TestSchemaUpgrade:
    def test_a_shared_installation_loses_its_accounts_but_keeps_its_registers(
        self, tmp_path: Path
    ) -> None:
        """The risky half of dropping accounts: an existing database must survive.

        Version 2 belonged to the shared deployment — users, sessions and author
        columns. Upgrading has to remove all of that without taking the saved
        registers and the run history with it.
        """
        path = tmp_path / "v2.sqlite3"
        legacy = sqlite3.connect(path)
        legacy.executescript(
            """
            CREATE TABLE schema_version (version INTEGER NOT NULL);
            INSERT INTO schema_version (version) VALUES (2);
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE registers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                register_id INTEGER REFERENCES registers(id) ON DELETE SET NULL,
                label TEXT NOT NULL,
                config TEXT NOT NULL,
                result TEXT NOT NULL,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );

            INSERT INTO users (id, email, full_name, password_hash, role, created_at)
                VALUES (1, 'awa@exemple.fr', 'Awa Diallo', 'scrypt$x', 'admin', '2026-08-23');
            INSERT INTO registers
                (id, name, payload, created_by, created_at, updated_by, updated_at)
                VALUES (1, 'Extension usine', '{"items": []}', 1, '2026-08-01', 1, '2026-08-02');
            INSERT INTO runs (id, register_id, label, config, result, created_by, created_at)
                VALUES (1, 1, 'Décision P80', '{"seed": 42}', '{"P80": 1500}', 1, '2026-08-03');
            """
        )
        legacy.commit()
        legacy.close()

        upgraded = database.connect(path)
        try:
            registers = projects.list_registers(upgraded)
            runs = projects.list_runs(upgraded)

            assert [item.name for item in registers] == ["Extension usine"]
            assert registers[0].created_at == "2026-08-01", "la date de création est conservée"
            assert [run.label for run in runs] == ["Décision P80"]
            assert runs[0].register_id == 1, "le lien registre/exécution survit"
            assert runs[0].config == {"seed": 42}

            remaining = {
                row[0]
                for row in upgraded.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            assert "users" not in remaining
            assert "sessions" not in remaining

            columns = {
                row[1] for row in upgraded.execute("PRAGMA table_info(registers)").fetchall()
            }
            assert "created_by" not in columns
            assert "updated_by" not in columns

            version = upgraded.execute("SELECT version FROM schema_version").fetchone()["version"]
            assert version == database.SCHEMA_VERSION

            # La base reste utilisable après migration.
            saved = projects.save_register(upgraded, name="Après migration", payload=PAYLOAD)
            assert saved.name == "Après migration"
        finally:
            upgraded.close()

    def test_a_fresh_database_starts_at_the_current_version(self, tmp_path: Path) -> None:
        handle = database.connect(tmp_path / "neuve.sqlite3")
        try:
            version = handle.execute("SELECT version FROM schema_version").fetchone()["version"]
            assert version == database.SCHEMA_VERSION
            assert projects.list_registers(handle) == []
        finally:
            handle.close()

    def test_a_version_one_database_loses_its_credentials(self, tmp_path: Path) -> None:
        """Version 1 held accounts and no registers at all.

        Requiring a registers table before cleaning up would skip this case and
        leave password and session-token hashes in a file the application can no
        longer manage — credentials outliving the feature that created them.
        """
        path = tmp_path / "v1.sqlite3"
        legacy = sqlite3.connect(path)
        legacy.executescript(
            """
            CREATE TABLE schema_version (version INTEGER NOT NULL);
            INSERT INTO schema_version (version) VALUES (1);
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            INSERT INTO users (email, full_name, password_hash, role, created_at)
                VALUES ('awa@exemple.fr', 'Awa Diallo', 'scrypt$secret', 'admin', '2026-08-23');
            INSERT INTO sessions (token_hash, user_id, created_at, expires_at)
                VALUES ('jeton', 1, '2026-08-23', '2026-08-24');
            """
        )
        legacy.commit()
        legacy.close()

        upgraded = database.connect(path)
        try:
            remaining = {
                row[0]
                for row in upgraded.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

            assert "users" not in remaining, "les empreintes de mot de passe doivent disparaître"
            assert "sessions" not in remaining
            assert {"registers", "runs"} <= remaining, "les nouvelles tables doivent exister"

            version = upgraded.execute("SELECT version FROM schema_version").fetchone()["version"]
            assert version == database.SCHEMA_VERSION
            assert projects.save_register(upgraded, name="Neuf", payload=PAYLOAD).id
        finally:
            upgraded.close()


class TestCounts:
    def test_counting_does_not_depend_on_the_listing_limit(
        self, connection: sqlite3.Connection
    ) -> None:
        """list_runs caps at 50 by default; a count that reused it would lie."""
        register = projects.save_register(connection, name="Extension usine", payload=PAYLOAD)
        for index in range(60):
            projects.save_run(
                connection,
                label=f"Run {index}",
                config=CONFIG,
                result=RESULT,
                register_id=register.id,
            )

        assert projects.count_registers(connection) == 1
        assert projects.count_runs(connection) == 60
        assert len(projects.list_runs(connection)) == 50, "la liste reste plafonnée"

    def test_an_empty_database_counts_zero(self, connection: sqlite3.Connection) -> None:
        assert projects.count_registers(connection) == 0
        assert projects.count_runs(connection) == 0
