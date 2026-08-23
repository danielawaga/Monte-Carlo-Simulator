"""Tests for the local account system backing the on-premises deployment."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from monte_carlo_simulator.storage import accounts, database
from monte_carlo_simulator.storage.accounts import AccountError


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    handle = database.connect(tmp_path / "test.sqlite3")
    try:
        yield handle
    finally:
        handle.close()


def _member(connection: sqlite3.Connection, email: str = "claire@exemple.fr") -> accounts.User:
    return accounts.create_user(
        connection,
        email=email,
        full_name="Claire Martin",
        password="motdepasse-solide",
    )


class TestDatabase:
    def test_data_directory_honours_the_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(database.DATA_DIR_ENV, "/srv/monte-carlo")
        assert database.data_directory() == Path("/srv/monte-carlo")

    def test_connecting_twice_keeps_the_existing_data(self, tmp_path: Path) -> None:
        path = tmp_path / "reopen.sqlite3"
        first = database.connect(path)
        _member(first)
        first.close()

        second = database.connect(path)
        try:
            assert [user.email for user in accounts.list_users(second)] == ["claire@exemple.fr"]
        finally:
            second.close()

    def test_schema_records_its_version_once(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute("SELECT version FROM schema_version").fetchall()
        assert [row["version"] for row in rows] == [database.SCHEMA_VERSION]


class TestAccountCreation:
    def test_first_admin_can_only_be_created_on_a_fresh_installation(
        self, connection: sqlite3.Connection
    ) -> None:
        assert accounts.has_any_user(connection) is False

        admin = accounts.create_first_admin(
            connection,
            email="Admin@Exemple.FR",
            full_name="Awa Diallo",
            password="motdepasse-solide",
        )
        assert admin.is_admin is True
        assert admin.email == "admin@exemple.fr", "l'adresse doit être normalisée"
        assert accounts.has_any_user(connection) is True

        with pytest.raises(AccountError, match="déjà initialisée"):
            accounts.create_first_admin(
                connection,
                email="autre@exemple.fr",
                full_name="Intrus",
                password="motdepasse-solide",
            )

    def test_duplicate_email_is_refused(self, connection: sqlite3.Connection) -> None:
        _member(connection)
        with pytest.raises(AccountError, match="existe déjà"):
            _member(connection)

    @pytest.mark.parametrize(
        ("email", "full_name", "password"),
        [
            ("sans-arobase", "Nom", "motdepasse-solide"),
            ("vide@exemple.fr", "   ", "motdepasse-solide"),
            ("court@exemple.fr", "Nom", "court"),
        ],
    )
    def test_invalid_input_is_refused(
        self, connection: sqlite3.Connection, email: str, full_name: str, password: str
    ) -> None:
        with pytest.raises(AccountError):
            accounts.create_user(connection, email=email, full_name=full_name, password=password)

    def test_password_is_never_stored_in_clear(self, connection: sqlite3.Connection) -> None:
        _member(connection)
        stored = connection.execute("SELECT password_hash FROM users").fetchone()["password_hash"]
        assert "motdepasse-solide" not in stored
        assert stored.startswith("scrypt$")


class TestAuthentication:
    def test_correct_password_authenticates_and_stamps_the_login(
        self, connection: sqlite3.Connection
    ) -> None:
        created = _member(connection)
        assert created.last_login_at is None

        user = accounts.authenticate(
            connection, email="CLAIRE@exemple.fr", password="motdepasse-solide"
        )

        assert user is not None
        assert user.id == created.id
        assert accounts.get_user(connection, created.id).last_login_at is not None

    @pytest.mark.parametrize(
        ("email", "password"),
        [
            ("claire@exemple.fr", "mauvais-mot-de-passe"),
            ("inconnu@exemple.fr", "motdepasse-solide"),
        ],
    )
    def test_wrong_credentials_are_refused(
        self, connection: sqlite3.Connection, email: str, password: str
    ) -> None:
        _member(connection)
        assert accounts.authenticate(connection, email=email, password=password) is None

    def test_a_disabled_account_cannot_authenticate(self, connection: sqlite3.Connection) -> None:
        user = _member(connection)
        # Un second compte admin évite que la garde du dernier administrateur
        # s'interpose dans ce test.
        accounts.create_user(
            connection,
            email="admin@exemple.fr",
            full_name="Awa Diallo",
            password="motdepasse-solide",
            role="admin",
        )
        accounts.set_active(connection, user.id, active=False)

        assert (
            accounts.authenticate(
                connection, email="claire@exemple.fr", password="motdepasse-solide"
            )
            is None
        )


class TestSessions:
    def test_a_session_resolves_to_its_user(self, connection: sqlite3.Connection) -> None:
        user = _member(connection)
        token = accounts.open_session(connection, user.id)

        resolved = accounts.user_for_session(connection, token)

        assert resolved is not None
        assert resolved.id == user.id

    def test_only_the_token_hash_is_stored(self, connection: sqlite3.Connection) -> None:
        user = _member(connection)
        token = accounts.open_session(connection, user.id)

        stored = connection.execute("SELECT token_hash FROM sessions").fetchone()["token_hash"]
        assert stored != token

    @pytest.mark.parametrize("token", ["", "jeton-invente"])
    def test_unknown_tokens_resolve_to_nobody(
        self, connection: sqlite3.Connection, token: str
    ) -> None:
        _member(connection)
        assert accounts.user_for_session(connection, token) is None

    def test_closing_a_session_invalidates_it(self, connection: sqlite3.Connection) -> None:
        user = _member(connection)
        token = accounts.open_session(connection, user.id)

        accounts.close_session(connection, token)

        assert accounts.user_for_session(connection, token) is None

    def test_an_expired_session_is_rejected_and_dropped(
        self, connection: sqlite3.Connection
    ) -> None:
        user = _member(connection)
        token = accounts.open_session(connection, user.id)
        connection.execute(
            "UPDATE sessions SET expires_at = ?",
            ((datetime.now(UTC) - timedelta(minutes=1)).isoformat(),),
        )

        assert accounts.user_for_session(connection, token) is None
        assert connection.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"] == 0

    def test_purging_removes_only_expired_sessions(self, connection: sqlite3.Connection) -> None:
        user = _member(connection)
        live = accounts.open_session(connection, user.id)
        stale = accounts.open_session(connection, user.id)
        connection.execute(
            "UPDATE sessions SET expires_at = ? WHERE token_hash != ?",
            (
                (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
                hashlib.sha256(live.encode()).hexdigest(),
            ),
        )

        assert accounts.purge_expired_sessions(connection) == 1
        assert accounts.user_for_session(connection, live) is not None
        assert accounts.user_for_session(connection, stale) is None

    def test_changing_the_password_revokes_open_sessions(
        self, connection: sqlite3.Connection
    ) -> None:
        user = _member(connection)
        token = accounts.open_session(connection, user.id)

        accounts.change_password(connection, user.id, new_password="nouveau-mot-de-passe")

        assert accounts.user_for_session(connection, token) is None
        assert (
            accounts.authenticate(connection, email=user.email, password="nouveau-mot-de-passe")
            is not None
        )

    def test_disabling_an_account_revokes_its_sessions(
        self, connection: sqlite3.Connection
    ) -> None:
        accounts.create_user(
            connection,
            email="admin@exemple.fr",
            full_name="Awa Diallo",
            password="motdepasse-solide",
            role="admin",
        )
        user = _member(connection)
        token = accounts.open_session(connection, user.id)

        accounts.set_active(connection, user.id, active=False)

        assert accounts.user_for_session(connection, token) is None


class TestAdministrationGuards:
    def test_the_last_administrator_cannot_be_disabled(
        self, connection: sqlite3.Connection
    ) -> None:
        admin = accounts.create_first_admin(
            connection,
            email="admin@exemple.fr",
            full_name="Awa Diallo",
            password="motdepasse-solide",
        )
        _member(connection)

        with pytest.raises(AccountError, match="dernier administrateur"):
            accounts.set_active(connection, admin.id, active=False)

    def test_the_last_administrator_cannot_be_demoted(self, connection: sqlite3.Connection) -> None:
        admin = accounts.create_first_admin(
            connection,
            email="admin@exemple.fr",
            full_name="Awa Diallo",
            password="motdepasse-solide",
        )

        with pytest.raises(AccountError, match="dernier administrateur"):
            accounts.set_role(connection, admin.id, role="member")

    def test_a_second_administrator_frees_the_guard(self, connection: sqlite3.Connection) -> None:
        first = accounts.create_first_admin(
            connection,
            email="admin@exemple.fr",
            full_name="Awa Diallo",
            password="motdepasse-solide",
        )
        promoted = accounts.set_role(connection, _member(connection).id, role="admin")

        assert promoted.is_admin is True
        assert accounts.count_active_admins(connection) == 2
        assert accounts.set_active(connection, first.id, active=False).is_active is False

    def test_operations_on_an_unknown_account_are_refused(
        self, connection: sqlite3.Connection
    ) -> None:
        with pytest.raises(AccountError, match="introuvable"):
            accounts.set_active(connection, 999, active=False)
        with pytest.raises(AccountError, match="introuvable"):
            accounts.set_role(connection, 999, role="admin")
        with pytest.raises(AccountError, match="introuvable"):
            accounts.change_password(connection, 999, new_password="motdepasse-solide")


class TestConcurrentSetup:
    def test_only_one_founding_admin_survives_a_race(self, tmp_path: Path) -> None:
        """Two first-run requests at once must not both produce an administrator.

        The connection is in autocommit, so an unguarded check-then-insert lets
        both callers read an empty table and both succeed — handing admin access
        to whoever races the legitimate installer on a public setup route.
        """
        path = tmp_path / "race.sqlite3"
        database.connect(path).close()
        start = threading.Barrier(2)
        outcomes: list[str] = []
        lock = threading.Lock()

        def attempt(email: str) -> None:
            handle = database.connect(path)
            try:
                start.wait(timeout=5)
                accounts.create_first_admin(
                    handle, email=email, full_name="Candidat", password="motdepasse-solide"
                )
                result = "créé"
            except AccountError:
                result = "refusé"
            finally:
                handle.close()
            with lock:
                outcomes.append(result)

        threads = [
            threading.Thread(target=attempt, args=(f"admin{index}@exemple.fr",))
            for index in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        assert sorted(outcomes) == ["créé", "refusé"]

        verification = database.connect(path)
        try:
            assert len(accounts.list_users(verification)) == 1
        finally:
            verification.close()

    def test_a_failed_setup_leaves_the_installation_open(self, tmp_path: Path) -> None:
        """A rejected attempt must roll back, not half-initialise the database."""
        path = tmp_path / "rollback.sqlite3"
        handle = database.connect(path)
        try:
            with pytest.raises(AccountError):
                accounts.create_first_admin(
                    handle, email="admin@exemple.fr", full_name="Awa", password="court"
                )

            assert accounts.has_any_user(handle) is False
            recovered = accounts.create_first_admin(
                handle,
                email="admin@exemple.fr",
                full_name="Awa Diallo",
                password="motdepasse-solide",
            )
            assert recovered.is_admin is True
        finally:
            handle.close()


class TestThreadHandover:
    def test_a_connection_survives_being_used_from_another_thread(self, tmp_path: Path) -> None:
        """FastAPI hands a synchronous dependency and its endpoint different threads.

        A connection that refuses to cross threads therefore fails the request as
        soon as the threadpool has more than one thread busy — which sequential
        command-line calls hide and a browser loading several assets exposes.
        """
        handle = database.connect(tmp_path / "handover.sqlite3")
        outcome: dict[str, object] = {}

        def read_from_another_thread() -> None:
            try:
                outcome["value"] = accounts.has_any_user(handle)
            except Exception as exc:  # noqa: BLE001 - the failure is the subject
                outcome["error"] = exc

        worker = threading.Thread(target=read_from_another_thread)
        worker.start()
        worker.join(timeout=10)
        handle.close()

        assert "error" not in outcome, (
            f"la connexion refuse de changer de fil : {outcome.get('error')}"
        )
        assert outcome["value"] is False
