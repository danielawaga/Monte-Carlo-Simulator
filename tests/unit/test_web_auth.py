"""Tests for session authentication and account administration over HTTP."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from monte_carlo_simulator.storage import database
from monte_carlo_simulator.web_api import app
from monte_carlo_simulator.web_auth import SESSION_COOKIE

ADMIN = {"email": "awa@exemple.fr", "fullName": "Awa Diallo", "password": "motdepasse-solide"}
MEMBER = {
    "email": "claire@exemple.fr",
    "fullName": "Claire Martin",
    "password": "motdepasse-solide",
}

PROTECTED_ROUTES = [
    ("get", "/api/template"),
    ("post", "/api/register/validate"),
    ("post", "/api/register/export"),
    ("post", "/api/register/simulate"),
    ("post", "/api/results/export"),
    ("post", "/api/results/export-bundle"),
    ("get", "/api/users"),
    ("get", "/api/auth/me"),
]


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(database.DATA_DIR_ENV, str(tmp_path / "data"))


@pytest.fixture
def anonymous() -> Iterator[TestClient]:
    with TestClient(app) as http:
        yield http


@pytest.fixture
def admin(anonymous: TestClient) -> TestClient:
    assert anonymous.post("/api/setup", json=ADMIN).status_code == 200
    return anonymous


@pytest.fixture
def member(admin: TestClient) -> Iterator[TestClient]:
    assert admin.post("/api/users", json=MEMBER).status_code == 200
    with TestClient(app) as http:
        assert (
            http.post(
                "/api/auth/login",
                json={"email": MEMBER["email"], "password": MEMBER["password"]},
            ).status_code
            == 200
        )
        yield http


class TestFirstRunSetup:
    def test_health_announces_that_setup_is_required(self, anonymous: TestClient) -> None:
        payload = anonymous.get("/api/health").json()

        assert payload["setupRequired"] is True
        assert payload["authenticated"] is False

    def test_setup_creates_the_admin_and_signs_them_in(self, anonymous: TestClient) -> None:
        response = anonymous.post("/api/setup", json=ADMIN)

        assert response.status_code == 200
        assert response.json()["user"]["role"] == "admin"
        assert SESSION_COOKIE in response.cookies
        assert anonymous.get("/api/health").json() == {
            "status": "ok",
            "engine": "monte-carlo-simulator",
            "setupRequired": False,
            "authenticated": True,
        }

    def test_setup_closes_once_an_account_exists(self, admin: TestClient) -> None:
        """The single most dangerous route: it must shut itself permanently."""
        with TestClient(app) as intruder:
            response = intruder.post(
                "/api/setup",
                json={
                    "email": "intrus@exemple.fr",
                    "fullName": "Intrus",
                    "password": "motdepasse-solide",
                },
            )

        assert response.status_code == 422
        assert "déjà initialisée" in response.json()["detail"]

    def test_setup_refuses_a_weak_password(self, anonymous: TestClient) -> None:
        response = anonymous.post("/api/setup", json={**ADMIN, "password": "court"})

        assert response.status_code == 422
        assert anonymous.get("/api/health").json()["setupRequired"] is True


class TestSignIn:
    def test_the_session_cookie_is_not_readable_by_javascript(self, anonymous: TestClient) -> None:
        """httpOnly is what stops an XSS bug from becoming stolen credentials."""
        response = anonymous.post("/api/setup", json=ADMIN)

        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie
        assert "samesite=lax" in cookie

    @pytest.mark.parametrize(
        ("email", "password"),
        [
            (ADMIN["email"], "mauvais-mot-de-passe"),
            ("inconnu@exemple.fr", "motdepasse-solide"),
        ],
    )
    def test_bad_credentials_are_refused_without_saying_why(
        self, admin: TestClient, email: str, password: str
    ) -> None:
        with TestClient(app) as http:
            response = http.post("/api/auth/login", json={"email": email, "password": password})

        assert response.status_code == 401
        assert response.json()["detail"] == "Identifiants invalides."

    def test_signing_out_invalidates_the_session(self, admin: TestClient) -> None:
        assert admin.get("/api/auth/me").status_code == 200

        assert admin.post("/api/auth/logout").status_code == 200

        assert admin.get("/api/auth/me").status_code == 401

    def test_a_forged_cookie_authenticates_nobody(self, admin: TestClient) -> None:
        with TestClient(app) as forger:
            forger.cookies.set(SESSION_COOKIE, "jeton-invente")
            assert forger.get("/api/auth/me").status_code == 401


class TestRouteProtection:
    @pytest.mark.parametrize(("method", "path"), PROTECTED_ROUTES)
    def test_every_business_route_requires_a_session(
        self, anonymous: TestClient, method: str, path: str
    ) -> None:
        anonymous.post("/api/setup", json=ADMIN)
        with TestClient(app) as stranger:
            call = getattr(stranger, method)
            response = call(path, json={}) if method == "post" else call(path)

        assert response.status_code == 401, f"{method.upper()} {path} est resté ouvert"

    def test_health_stays_public_for_deployment_probes(self, admin: TestClient) -> None:
        with TestClient(app) as stranger:
            assert stranger.get("/api/health").status_code == 200

    def test_a_signed_in_member_reaches_the_simulator(self, member: TestClient) -> None:
        assert member.get("/api/template").status_code == 200


class TestAdministration:
    def test_a_member_cannot_administer_accounts(self, member: TestClient) -> None:
        """403 and not 401: the request is authenticated, merely not allowed."""
        listing = member.get("/api/users")
        creation = member.post(
            "/api/users",
            json={"email": "x@exemple.fr", "fullName": "X", "password": "motdepasse-solide"},
        )

        assert listing.status_code == 403
        assert creation.status_code == 403

    def test_an_admin_lists_and_creates_accounts(self, admin: TestClient) -> None:
        created = admin.post("/api/users", json=MEMBER)
        assert created.status_code == 200
        assert created.json()["user"]["role"] == "member"

        users = admin.get("/api/users").json()["users"]
        assert [user["email"] for user in users] == [ADMIN["email"], MEMBER["email"]]
        assert all("password" not in key.lower() for user in users for key in user)

    def test_a_duplicate_address_is_refused(self, admin: TestClient) -> None:
        admin.post("/api/users", json=MEMBER)

        assert admin.post("/api/users", json=MEMBER).status_code == 422

    def test_disabling_an_account_locks_its_open_session_out(
        self, admin: TestClient, member: TestClient
    ) -> None:
        assert member.get("/api/auth/me").status_code == 200
        member_id = next(
            user["id"]
            for user in admin.get("/api/users").json()["users"]
            if user["email"] == MEMBER["email"]
        )

        response = admin.patch(f"/api/users/{member_id}", json={"isActive": False})

        assert response.status_code == 200
        assert response.json()["user"]["isActive"] is False
        assert member.get("/api/auth/me").status_code == 401

    def test_the_last_administrator_is_protected(self, admin: TestClient) -> None:
        admin_id = admin.get("/api/auth/me").json()["user"]["id"]

        demote = admin.patch(f"/api/users/{admin_id}", json={"role": "member"})
        disable = admin.patch(f"/api/users/{admin_id}", json={"isActive": False})

        assert demote.status_code == 422
        assert disable.status_code == 422
        assert admin.get("/api/auth/me").json()["user"]["role"] == "admin"

    def test_updating_an_unknown_account_reports_404(self, admin: TestClient) -> None:
        assert admin.patch("/api/users/999", json={"role": "member"}).status_code == 404


class TestOwnPassword:
    def test_changing_the_password_requires_the_current_one(self, admin: TestClient) -> None:
        response = admin.post(
            "/api/account/password",
            json={"currentPassword": "mauvais", "newPassword": "nouveau-mot-de-passe"},
        )

        assert response.status_code == 403

    def test_a_successful_change_keeps_the_author_signed_in(self, admin: TestClient) -> None:
        response = admin.post(
            "/api/account/password",
            json={
                "currentPassword": ADMIN["password"],
                "newPassword": "nouveau-mot-de-passe",
            },
        )

        assert response.status_code == 200
        assert admin.get("/api/auth/me").status_code == 200, "l'auteur ne doit pas être déconnecté"

    def test_the_change_logs_other_browsers_out(self, admin: TestClient) -> None:
        with TestClient(app) as other_browser:
            other_browser.post(
                "/api/auth/login",
                json={"email": ADMIN["email"], "password": ADMIN["password"]},
            )
            assert other_browser.get("/api/auth/me").status_code == 200

            admin.post(
                "/api/account/password",
                json={
                    "currentPassword": ADMIN["password"],
                    "newPassword": "nouveau-mot-de-passe",
                },
            )

            assert other_browser.get("/api/auth/me").status_code == 401
