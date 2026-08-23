"""Tests for shared registers and runs over HTTP."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from monte_carlo_simulator.storage import database
from monte_carlo_simulator.web_api import app

ADMIN = {"email": "awa@exemple.fr", "fullName": "Awa Diallo", "password": "motdepasse-solide"}
MEMBER = {
    "email": "claire@exemple.fr",
    "fullName": "Claire Martin",
    "password": "motdepasse-solide",
}

DRAFT: dict[str, object] = {
    "schemaVersion": "1.0",
    "metadata": {
        "projectName": "Extension usine",
        "analysisType": "cost",
        "defaultUnit": "EUR",
        "baselineEstimate": 2500,
        "description": "",
    },
    "items": [
        {
            "id": "risk-1",
            "name": "Études",
            "distribution": "triangular",
            "minimum": 100,
            "mostLikely": 150,
            "maximum": 250,
            "category": "Ingénierie",
            "unit": "EUR",
            "enabled": True,
            "notes": "",
        }
    ],
    "correlations": {"mode": "independent", "names": [], "values": []},
}
CONFIG: dict[str, object] = {
    "simulations": 10_000,
    "seed": 42,
    "levels": [50, 80, 90, 95],
    "decisionPercentile": 80,
    "exceedanceThreshold": 3000,
    "convergenceTolerance": 1,
}


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(database.DATA_DIR_ENV, str(tmp_path / "data"))


@pytest.fixture
def admin() -> Iterator[TestClient]:
    with TestClient(app) as http:
        assert http.post("/api/setup", json=ADMIN).status_code == 200
        yield http


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


def _save(client: TestClient, name: str, register_id: int | None = None) -> dict[str, object]:
    body: dict[str, object] = {"name": name, "register": DRAFT}
    if register_id is not None:
        body["registerId"] = register_id
    response = client.post("/api/registers", json=body)
    assert response.status_code == 200, response.text
    return response.json()["register"]


class TestSharedRegisters:
    def test_a_saved_register_carries_its_author(self, admin: TestClient) -> None:
        stored = _save(admin, "Extension usine")

        assert stored["name"] == "Extension usine"
        assert stored["createdBy"]["fullName"] == "Awa Diallo"
        assert stored["register"]["metadata"]["projectName"] == "Extension usine"

    def test_a_colleague_sees_and_continues_the_same_register(
        self, admin: TestClient, member: TestClient
    ) -> None:
        """The whole point of the shared instance, exercised end to end."""
        original = _save(admin, "Extension usine")

        listing = member.get("/api/registers").json()["registers"]
        assert [item["id"] for item in listing] == [original["id"]]

        updated = _save(member, "Extension usine — révisé", register_id=original["id"])

        assert updated["createdBy"]["fullName"] == "Awa Diallo"
        assert updated["updatedBy"]["fullName"] == "Claire Martin"

    def test_an_unknown_register_reports_404(self, admin: TestClient) -> None:
        assert admin.get("/api/registers/999").status_code == 404

    def test_an_empty_name_is_refused(self, admin: TestClient) -> None:
        response = admin.post("/api/registers", json={"name": "   ", "register": DRAFT})

        assert response.status_code == 422

    def test_a_stranger_reaches_nothing(self, admin: TestClient) -> None:
        _save(admin, "Extension usine")
        with TestClient(app) as stranger:
            assert stranger.get("/api/registers").status_code == 401
            assert stranger.post("/api/registers", json={}).status_code == 401
            assert stranger.get("/api/runs").status_code == 401


class TestSharedRuns:
    def test_a_run_is_kept_with_its_assumptions_and_author(self, admin: TestClient) -> None:
        register = _save(admin, "Extension usine")

        response = admin.post(
            "/api/runs",
            json={
                "label": "Référence",
                "config": CONFIG,
                "result": {"summary": {"mean": 1234.5}},
                "registerId": register["id"],
            },
        )

        assert response.status_code == 200
        run = response.json()["run"]
        assert run["createdBy"]["fullName"] == "Awa Diallo"
        assert run["config"]["seed"] == 42
        assert run["result"]["summary"]["mean"] == 1234.5

    def test_runs_can_be_filtered_by_register(self, admin: TestClient) -> None:
        first = _save(admin, "Projet A")
        second = _save(admin, "Projet B")
        for register, label in ((first, "Run A"), (second, "Run B")):
            admin.post(
                "/api/runs",
                json={
                    "label": label,
                    "config": CONFIG,
                    "result": {},
                    "registerId": register["id"],
                },
            )

        filtered = admin.get("/api/runs", params={"register_id": first["id"]}).json()["runs"]

        assert [run["label"] for run in filtered] == ["Run A"]
        assert len(admin.get("/api/runs").json()["runs"]) == 2

    def test_a_member_can_record_a_run(self, member: TestClient) -> None:
        response = member.post(
            "/api/runs", json={"label": "Mitigation", "config": CONFIG, "result": {}}
        )

        assert response.status_code == 200
        assert response.json()["run"]["createdBy"]["fullName"] == "Claire Martin"


class TestDeletionIsReserved:
    def test_a_member_cannot_delete_a_shared_register(
        self, admin: TestClient, member: TestClient
    ) -> None:
        """Editing is everyone's business; destroying shared work is not."""
        register = _save(admin, "Extension usine")

        response = member.delete(f"/api/registers/{register['id']}")

        assert response.status_code == 403
        assert len(member.get("/api/registers").json()["registers"]) == 1

    def test_an_admin_deletes_the_register_but_keeps_its_runs(self, admin: TestClient) -> None:
        register = _save(admin, "Extension usine")
        run = admin.post(
            "/api/runs",
            json={
                "label": "Décision P80",
                "config": CONFIG,
                "result": {},
                "registerId": register["id"],
            },
        ).json()["run"]

        assert admin.delete(f"/api/registers/{register['id']}").status_code == 200

        assert admin.get("/api/registers").json()["registers"] == []
        survivors = admin.get("/api/runs").json()["runs"]
        assert [item["id"] for item in survivors] == [run["id"]]
        assert survivors[0]["registerId"] is None

    def test_deleting_an_unknown_register_is_refused(self, admin: TestClient) -> None:
        assert admin.delete("/api/registers/999").status_code == 422
