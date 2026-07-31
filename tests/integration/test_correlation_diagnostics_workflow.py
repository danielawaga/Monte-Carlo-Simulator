from pathlib import Path

import pandas as pd

from monte_carlo_simulator.application import run_simulation_from_excel
from monte_carlo_simulator.models import SimulationConfig
from scripts.generate_correlated_cost_register import generate


def test_correlated_excel_workflow_exports_strict_diagnostics(tmp_path: Path) -> None:
    input_path = generate(tmp_path / "correlated.xlsx")

    run = run_simulation_from_excel(
        input_path,
        SimulationConfig(number_of_simulations=500, random_seed=42),
        tmp_path / "output",
    )

    assert run.correlation_diagnostics_path is not None
    assert run.correlation_diagnostics_path.exists()
    assert run.correlation_diagnostics_path in run.artifact_paths

    diagnostics = pd.read_csv(run.correlation_diagnostics_path)
    assert diagnostics.loc[0, "dimension"] == 7
    assert diagnostics.loc[0, "minimum_eigenvalue"] > 0
    assert diagnostics.loc[0, "policy"] == "strict-no-repair"
    assert not bool(diagnostics.loc[0, "automatic_repair_applied"])
