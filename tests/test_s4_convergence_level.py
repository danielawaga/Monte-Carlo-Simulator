"""Integration checks for the S4 decision-level convergence workflow."""

from pathlib import Path

import pandas as pd

from monte_carlo_simulator.application.service import run_simulation_from_excel
from monte_carlo_simulator.models import SimulationConfig

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "data" / "templates" / "risk_register_template.xlsx"


def test_excel_workflow_can_target_selected_convergence_level(tmp_path: Path) -> None:
    run = run_simulation_from_excel(
        TEMPLATE_PATH,
        config=SimulationConfig(
            number_of_simulations=200,
            random_seed=42,
            confidence_levels=(0.50, 0.80, 0.90),
        ),
        output_dir=tmp_path,
        convergence_confidence_level=0.80,
    )

    diagnostics = pd.read_csv(run.convergence_path)

    assert set(diagnostics["target_percentile"]) == {"P80"}
    assert diagnostics["draw_count"].iloc[-1] == 200
