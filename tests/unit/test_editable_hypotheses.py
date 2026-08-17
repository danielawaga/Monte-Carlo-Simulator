"""Tests for the Excel-to-editable-model boundary used by the UI."""

from pathlib import Path

from monte_carlo_simulator.application.hypotheses import load_editable_risk_register
from monte_carlo_simulator.io import create_risk_register_workbook


def test_excel_register_becomes_editable_rows_and_keeps_disabled_items(tmp_path: Path) -> None:
    path = tmp_path / "editable.xlsx"
    create_risk_register_workbook(
        path,
        metadata_values={
            "project_name": "Scénario importé",
            "analysis_type": "cost",
            "default_unit": "EUR",
            "baseline_estimate": 1_000,
        },
        risk_rows=[
            {
                "name": "Actif",
                "distribution": "triangular",
                "minimum": 10,
                "most_likely": 20,
                "maximum": 40,
                "enabled": True,
            },
            {
                "name": "Option désactivée",
                "distribution": "event",
                "probability": 0.2,
                "impact": 100,
                "enabled": False,
            },
        ],
    )

    editable = load_editable_risk_register(path)

    assert editable.metadata.project_name == "Scénario importé"
    assert editable.metadata.baseline_estimate == 1_000
    assert editable.rows["name"].tolist() == ["Actif", "Option désactivée"]
    assert editable.rows["enabled"].tolist() == [True, False]
    assert "_excel_row" not in editable.rows
