"""Tests for saved registers and the run history over HTTP."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from monte_carlo_simulator.storage import database
from monte_carlo_simulator.web_api import app

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
    """Point every test at its own database.

    Without this the suite would write into the real per-machine data directory
    of whoever runs it.
    """
    monkeypatch.setenv(database.DATA_DIR_ENV, str(tmp_path / "data"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as http:
        yield http


def _save(client: TestClient, name: str, register_id: int | None = None) -> dict[str, object]:
    body: dict[str, object] = {"name": name, "register": DRAFT}
    if register_id is not None:
        body["registerId"] = register_id
    response = client.post("/api/registers", json=body)
    assert response.status_code == 200, response.text
    return response.json()["register"]


class TestSavedRegisters:
    def test_health_reports_a_working_engine(self, client: TestClient) -> None:
        assert client.get("/api/health").json() == {
            "status": "ok",
            "engine": "monte-carlo-simulator",
        }

    def test_a_register_survives_the_round_trip(self, client: TestClient) -> None:
        stored = _save(client, "Extension usine")

        reloaded = client.get(f"/api/registers/{stored['id']}").json()["register"]

        assert reloaded["name"] == "Extension usine"
        assert reloaded["register"]["metadata"]["projectName"] == "Extension usine"
        assert reloaded["register"]["items"][0]["name"] == "Études"

    def test_saving_over_an_existing_register_replaces_it(self, client: TestClient) -> None:
        original = _save(client, "Extension usine")

        updated = _save(client, "Extension usine — révisé", register_id=original["id"])

        assert updated["id"] == original["id"]
        assert updated["createdAt"] == original["createdAt"]
        assert [item["name"] for item in client.get("/api/registers").json()["registers"]] == [
            "Extension usine — révisé"
        ]

    def test_an_unknown_register_reports_404(self, client: TestClient) -> None:
        assert client.get("/api/registers/999").status_code == 404

    def test_an_empty_name_is_refused(self, client: TestClient) -> None:
        response = client.post("/api/registers", json={"name": "   ", "register": DRAFT})

        assert response.status_code == 422
        assert client.get("/api/registers").json()["registers"] == []


class TestRunHistory:
    def test_a_run_is_kept_with_the_assumptions_it_came_from(self, client: TestClient) -> None:
        """What lets a figure sent to a client be traced back to its inputs."""
        register = _save(client, "Extension usine")

        response = client.post(
            "/api/runs",
            json={
                "label": "Décision P80",
                "config": CONFIG,
                "result": {"summary": {"P80": 123978}},
                "registerId": register["id"],
            },
        )

        assert response.status_code == 200
        run = response.json()["run"]
        assert run["config"]["seed"] == 42
        assert run["result"]["summary"]["P80"] == 123978
        assert run["registerId"] == register["id"]
        assert run["createdAt"]

    def test_runs_can_be_filtered_by_register(self, client: TestClient) -> None:
        first = _save(client, "Projet A")
        second = _save(client, "Projet B")
        for register, label in ((first, "Run A"), (second, "Run B")):
            client.post(
                "/api/runs",
                json={
                    "label": label,
                    "config": CONFIG,
                    "result": {},
                    "registerId": register["id"],
                },
            )

        filtered = client.get("/api/runs", params={"register_id": first["id"]}).json()["runs"]

        assert [run["label"] for run in filtered] == ["Run A"]
        assert len(client.get("/api/runs").json()["runs"]) == 2

    def test_a_run_needs_no_register(self, client: TestClient) -> None:
        response = client.post(
            "/api/runs", json={"label": "Essai rapide", "config": CONFIG, "result": {}}
        )

        assert response.status_code == 200
        assert response.json()["run"]["registerId"] is None


class TestDeletion:
    def test_deleting_a_register_keeps_the_runs_it_produced(self, client: TestClient) -> None:
        """A decision record must not vanish when its source is tidied away."""
        register = _save(client, "Extension usine")
        run = client.post(
            "/api/runs",
            json={
                "label": "Décision P80",
                "config": CONFIG,
                "result": {},
                "registerId": register["id"],
            },
        ).json()["run"]

        assert client.delete(f"/api/registers/{register['id']}").status_code == 200

        assert client.get("/api/registers").json()["registers"] == []
        survivors = client.get("/api/runs").json()["runs"]
        assert [item["id"] for item in survivors] == [run["id"]]
        assert survivors[0]["registerId"] is None

    def test_deleting_an_unknown_register_is_refused(self, client: TestClient) -> None:
        assert client.delete("/api/registers/999").status_code == 422


class TestStorageLocation:
    def test_it_reports_where_the_data_lives_and_how_much(self, client: TestClient) -> None:
        """The interface has no other way to name the file worth backing up."""
        empty = client.get("/api/storage").json()

        assert empty["registers"] == 0
        assert empty["runs"] == 0
        assert empty["databasePath"].endswith(database.DATABASE_FILENAME)

        register = _save(client, "Extension usine")
        client.post(
            "/api/runs",
            json={
                "label": "Décision P80",
                "config": CONFIG,
                "result": {},
                "registerId": register["id"],
            },
        )

        filled = client.get("/api/storage").json()
        assert filled["registers"] == 1
        assert filled["runs"] == 1
        assert filled["databasePath"] == empty["databasePath"]
