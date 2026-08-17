from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import SimulationConfig
from monte_carlo_simulator.web_api import (
    _histogram_payload,
    _parse_confidence_levels,
    _records,
    _s_curve_payload,
    app,
)


def test_parse_confidence_levels() -> None:
    assert _parse_confidence_levels("0.5, 0.8,0.95") == (0.5, 0.8, 0.95)


def test_parse_confidence_levels_rejects_non_numeric_values() -> None:
    with pytest.raises(ValidationError, match="comma-separated"):
        _parse_confidence_levels("0.5,P90")


def test_records_converts_numpy_scalars_and_nan() -> None:
    frame = pd.DataFrame([{"amount": np.float64(12.5), "rank": np.int64(2), "gap": np.nan}])
    assert _records(frame) == [{"amount": 12.5, "rank": 2, "gap": None}]


def test_histogram_payload_preserves_sample_count() -> None:
    samples = np.array([1.0, 2.0, 2.5, 3.0, 5.0])
    payload = _histogram_payload(samples, bins=3)
    assert sum(int(row["count"]) for row in payload) == len(samples)
    assert len(payload) == 3


def test_s_curve_payload_is_ordered_and_bounded() -> None:
    payload = _s_curve_payload(np.array([5.0, 1.0, 3.0]), points=3)
    assert [row["amount"] for row in payload] == [1.0, 3.0, 5.0]
    assert payload[0]["probability"] == 0.0
    assert payload[-1]["probability"] == 1.0


def _fake_run(output_dir: Path) -> SimpleNamespace:
    percentile = output_dir / "percentiles.csv"
    sensitivity = output_dir / "sensitivity.csv"
    convergence = output_dir / "convergence.csv"
    baseline = output_dir / "baseline.csv"

    pd.DataFrame(
        [
            {
                "percentile": "P80",
                "confidence_level": 0.8,
                "amount": 125.0,
                "recommended_reserve": 25.0,
                "unit": "MAD",
            }
        ]
    ).to_csv(percentile, index=False)
    pd.DataFrame(
        [
            {
                "item_name": "Structure",
                "spearman_rho": 0.72,
                "absolute_rho": 0.72,
                "rank": 1,
                "direction": "positive",
                "is_defined": True,
                "undefined_reason": "",
            }
        ]
    ).to_csv(sensitivity, index=False)
    pd.DataFrame([{"sample_size": 10000, "estimate": 130.0}]).to_csv(
        convergence, index=False
    )
    pd.DataFrame([{"baseline": 100.0, "exceedance_probability": 0.64}]).to_csv(
        baseline, index=False
    )

    return SimpleNamespace(
        result=SimpleNamespace(
            samples=np.array([90.0, 100.0, 115.0, 130.0, 150.0]),
            summary=pd.DataFrame(
                [
                    {
                        "mean": 117.0,
                        "median": 115.0,
                        "std": 21.0,
                        "minimum": 90.0,
                        "maximum": 150.0,
                        "P50": 115.0,
                        "P80": 134.0,
                        "P90": 142.0,
                        "P95": 146.0,
                    }
                ]
            ),
        ),
        metadata=SimpleNamespace(
            project_name="Projet test",
            analysis_type="cost",
            default_unit="MAD",
            baseline_estimate=100.0,
            description="Cas synthétique",
        ),
        percentile_table_path=percentile,
        sensitivity_path=sensitivity,
        convergence_path=convergence,
        baseline_comparison_path=baseline,
        correlation_diagnostics_path=None,
    )


def test_simulate_endpoint_serializes_existing_application_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_service(
        source: Path, config: SimulationConfig, output_dir: Path, **_: object
    ) -> SimpleNamespace:
        assert source.exists()
        assert output_dir.exists()
        assert config.number_of_simulations == 10_000
        return _fake_run(output_dir)

    monkeypatch.setattr("monte_carlo_simulator.web_api.run_simulation_from_excel", fake_service)
    client = TestClient(app)
    response = client.post(
        "/api/simulate",
        files={
            "file": (
                "risk_register.xlsx",
                b"not-a-real-workbook-because-service-is-mocked",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "simulations": "10000",
            "seed": "42",
            "confidence_levels": "0.5,0.8,0.9,0.95",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["name"] == "Projet test"
    assert payload["summary"]["P90"] == 142.0
    assert payload["baselineComparison"][0]["exceedance_probability"] == 0.64
    assert sum(bin_["count"] for bin_ in payload["histogram"]) == 5


def test_simulate_endpoint_rejects_non_xlsx_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/simulate",
        files={"file": ("risk_register.csv", b"x", "text/csv")},
    )
    assert response.status_code == 415
