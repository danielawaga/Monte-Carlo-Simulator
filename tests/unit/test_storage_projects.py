"""Tests for shared registers and runs, and for the authorship they record."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from monte_carlo_simulator.storage import accounts, database, projects
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


@pytest.fixture
def awa(connection: sqlite3.Connection) -> accounts.User:
    return accounts.create_first_admin(
        connection, email="awa@exemple.fr", full_name="Awa Diallo", password="motdepasse-solide"
    )


@pytest.fixture
def claire(connection: sqlite3.Connection, awa: accounts.User) -> accounts.User:
    return accounts.create_user(
        connection,
        email="claire@exemple.fr",
        full_name="Claire Martin",
        password="motdepasse-solide",
    )


class TestRegisters:
    def test_saving_records_its_author(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        stored = projects.save_register(
            connection, name="Extension usine", payload=PAYLOAD, author_id=awa.id
        )

        assert stored.name == "Extension usine"
        assert stored.payload == PAYLOAD
        assert stored.created_by.full_name == "Awa Diallo"
        assert stored.updated_by.full_name == "Awa Diallo"

    def test_a_colleague_can_pick_up_and_update_the_same_register(
        self, connection: sqlite3.Connection, awa: accounts.User, claire: accounts.User
    ) -> None:
        """The point of sharing: two people, one register, both traceable."""
        original = projects.save_register(
            connection, name="Extension usine", payload=PAYLOAD, author_id=awa.id
        )

        edited = projects.save_register(
            connection,
            name="Extension usine — révisé",
            payload={**PAYLOAD, "items": []},
            author_id=claire.id,
            register_id=original.id,
        )

        assert edited.id == original.id
        assert edited.name == "Extension usine — révisé"
        assert edited.created_by.full_name == "Awa Diallo", "le créateur ne doit pas être écrasé"
        assert edited.updated_by.full_name == "Claire Martin"

    def test_everyone_sees_every_register(
        self, connection: sqlite3.Connection, awa: accounts.User, claire: accounts.User
    ) -> None:
        projects.save_register(connection, name="Projet A", payload=PAYLOAD, author_id=awa.id)
        projects.save_register(connection, name="Projet B", payload=PAYLOAD, author_id=claire.id)

        listing = projects.list_registers(connection)

        assert {register.name for register in listing} == {"Projet A", "Projet B"}

    @pytest.mark.parametrize("name", ["", "   ", "x" * (projects.MAX_NAME_LENGTH + 1)])
    def test_an_unusable_name_is_refused(
        self, connection: sqlite3.Connection, awa: accounts.User, name: str
    ) -> None:
        with pytest.raises(ProjectError):
            projects.save_register(connection, name=name, payload=PAYLOAD, author_id=awa.id)

    def test_updating_an_unknown_register_is_refused(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        with pytest.raises(ProjectError, match="introuvable"):
            projects.save_register(
                connection, name="Fantôme", payload=PAYLOAD, author_id=awa.id, register_id=999
            )

    def test_an_accented_payload_survives_the_round_trip(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        payload = {"metadata": {"projectName": "Réhabilitation à Ouagadougou — phase 2"}}

        stored = projects.save_register(
            connection, name="Accents", payload=payload, author_id=awa.id
        )

        assert projects.get_register(connection, stored.id).payload == payload


class TestRuns:
    def test_a_run_records_its_author_and_assumptions(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        register = projects.save_register(
            connection, name="Extension usine", payload=PAYLOAD, author_id=awa.id
        )

        run = projects.save_run(
            connection,
            label="Référence",
            config=CONFIG,
            result=RESULT,
            author_id=awa.id,
            register_id=register.id,
        )

        assert run.created_by.full_name == "Awa Diallo"
        assert run.config == CONFIG
        assert run.result == RESULT
        assert run.register_id == register.id

    def test_runs_can_be_narrowed_to_one_register(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        first = projects.save_register(connection, name="A", payload=PAYLOAD, author_id=awa.id)
        second = projects.save_register(connection, name="B", payload=PAYLOAD, author_id=awa.id)
        projects.save_run(
            connection,
            label="Run A",
            config=CONFIG,
            result=RESULT,
            author_id=awa.id,
            register_id=first.id,
        )
        projects.save_run(
            connection,
            label="Run B",
            config=CONFIG,
            result=RESULT,
            author_id=awa.id,
            register_id=second.id,
        )

        assert [run.label for run in projects.list_runs(connection, register_id=first.id)] == [
            "Run A"
        ]
        assert len(projects.list_runs(connection)) == 2

    def test_a_run_attached_to_an_unknown_register_is_refused(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        with pytest.raises(ProjectError, match="introuvable"):
            projects.save_run(
                connection,
                label="Orphelin",
                config=CONFIG,
                result=RESULT,
                author_id=awa.id,
                register_id=999,
            )


class TestHistorySurvives:
    def test_deleting_a_register_keeps_the_runs_it_produced(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        """A decision record must not vanish when its source is tidied away."""
        register = projects.save_register(
            connection, name="Obsolète", payload=PAYLOAD, author_id=awa.id
        )
        run = projects.save_run(
            connection,
            label="Décision P80",
            config=CONFIG,
            result=RESULT,
            author_id=awa.id,
            register_id=register.id,
        )

        projects.delete_register(connection, register.id)

        survivor = projects.get_run(connection, run.id)
        assert survivor is not None
        assert survivor.label == "Décision P80"
        assert survivor.register_id is None, "le lien est coupé, pas l'exécution"
        assert survivor.created_by.full_name == "Awa Diallo"

    def test_authorship_stays_readable_after_the_account_is_removed(
        self, connection: sqlite3.Connection, awa: accounts.User, claire: accounts.User
    ) -> None:
        """Traceability has to outlive the person leaving the company."""
        register = projects.save_register(
            connection, name="Extension usine", payload=PAYLOAD, author_id=claire.id
        )
        run = projects.save_run(
            connection, label="Référence", config=CONFIG, result=RESULT, author_id=claire.id
        )

        connection.execute("DELETE FROM users WHERE id = ?", (claire.id,))

        assert projects.get_register(connection, register.id).created_by.id is None
        assert (
            projects.get_register(connection, register.id).created_by.full_name == "Compte supprimé"
        )
        assert projects.get_run(connection, run.id).label == "Référence"

    def test_deleting_an_unknown_register_is_refused(
        self, connection: sqlite3.Connection, awa: accounts.User
    ) -> None:
        with pytest.raises(ProjectError, match="introuvable"):
            projects.delete_register(connection, 999)


class TestSchemaUpgrade:
    def test_a_version_one_database_gains_the_new_tables(self, tmp_path: Path) -> None:
        """An installation created before this change must keep working."""
        path = tmp_path / "legacy.sqlite3"
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
                role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            """
        )
        legacy.commit()
        legacy.close()

        upgraded = database.connect(path)
        try:
            admin = accounts.create_first_admin(
                upgraded,
                email="awa@exemple.fr",
                full_name="Awa Diallo",
                password="motdepasse-solide",
            )
            stored = projects.save_register(
                upgraded, name="Après migration", payload=PAYLOAD, author_id=admin.id
            )

            assert stored.name == "Après migration"
            version = upgraded.execute("SELECT version FROM schema_version").fetchone()["version"]
            assert version == database.SCHEMA_VERSION
        finally:
            upgraded.close()
