import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from monte_carlo_simulator.application import run_simulation_from_excel
from monte_carlo_simulator.cli import main
from monte_carlo_simulator.io import create_risk_register_template
from monte_carlo_simulator.models import SimulationConfig


def test_end_to_end_excel_simulation_creates_artifacts(tmp_path: Path) -> None:
    input_path = create_risk_register_template(tmp_path / "risk_register.xlsx")
    output_dir = tmp_path / "output"
    config = SimulationConfig(
        number_of_simulations=750,
        random_seed=42,
        confidence_levels=(0.5, 0.951, 0.995),
    )

    run = run_simulation_from_excel(input_path, config, output_dir)

    assert run.metadata.project_name == "Fictitious Infrastructure Project"
    assert run.metadata.baseline_estimate == 250_000
    assert len(run.result.samples) == 750
    assert list(run.result.item_samples.columns) == [
        "Preliminary studies",
        "Detailed design",
        "Permitting",
        "Site supervision",
        "Commodity escalation",
        "Regulatory change",
    ]
    assert {"P50", "P95.1", "P99.5"} <= set(run.result.summary.columns)
    assert run.histogram_path.exists()
    assert run.summary_path.exists()
    assert run.sensitivity_path is not None and run.sensitivity_path.exists()
    assert run.tornado_path is not None and run.tornado_path.exists()
    assert run.baseline_comparison_path is not None
    assert run.baseline_comparison_path.exists()
    assert run.artifact_paths == (
        run.histogram_path,
        run.summary_path,
        run.sensitivity_path,
        run.tornado_path,
        run.baseline_comparison_path,
    )
    saved_comparison = pd.read_csv(run.baseline_comparison_path)
    assert saved_comparison.loc[0, "baseline"] == 250_000
    assert saved_comparison.loc[0, "exceedance_probability"] == pytest.approx(
        np.mean(run.result.samples > 250_000)
    )
    saved_sensitivity = pd.read_csv(run.sensitivity_path)
    assert list(saved_sensitivity.columns) == [
        "item_name",
        "spearman_rho",
        "absolute_rho",
        "rank",
        "direction",
        "is_defined",
        "undefined_reason",
    ]
    assert saved_sensitivity["rank"].dropna().is_monotonic_increasing
    saved_summary = pd.read_csv(run.summary_path)
    pd.testing.assert_frame_equal(saved_summary, run.result.summary)


def test_excel_simulation_is_reproducible_with_the_same_seed(tmp_path: Path) -> None:
    input_path = create_risk_register_template(tmp_path / "risk_register.xlsx")
    config = SimulationConfig(number_of_simulations=500, random_seed=8675309)

    first = run_simulation_from_excel(input_path, config, tmp_path / "first")
    second = run_simulation_from_excel(input_path, config, tmp_path / "second")

    np.testing.assert_array_equal(first.result.samples, second.result.samples)
    pd.testing.assert_frame_equal(first.result.item_samples, second.result.item_samples)
    pd.testing.assert_frame_equal(first.result.summary, second.result.summary)


def test_excel_simulation_without_baseline_skips_comparison_artifact(
    excel_workbook_factory, tmp_path: Path
) -> None:
    input_path = excel_workbook_factory(metadata={"baseline_estimate": None})

    run = run_simulation_from_excel(
        input_path,
        SimulationConfig(number_of_simulations=50, random_seed=42),
        tmp_path / "output",
    )

    assert run.baseline_comparison_path is None
    assert not (tmp_path / "output" / "baseline_comparison.csv").exists()


def test_cli_runs_from_excel_input(tmp_path: Path) -> None:
    input_path = create_risk_register_template(tmp_path / "risk_register.xlsx")
    output_dir = tmp_path / "cli-output"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "monte_carlo_simulator.cli",
            "--input",
            str(input_path),
            "--simulations",
            "250",
            "--seed",
            "42",
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Monte Carlo simulation completed." in completed.stdout
    assert "Fictitious Infrastructure Project" in completed.stdout
    assert "Sensitivity saved to:" in completed.stdout
    assert "Tornado chart saved to:" in completed.stdout
    assert "Baseline comparison saved to:" in completed.stdout
    assert (output_dir / "simulation_histogram.png").exists()
    assert (output_dir / "simulation_summary.csv").exists()
    assert (output_dir / "sensitivity_summary.csv").exists()
    assert (output_dir / "sensitivity_tornado.png").exists()
    assert (output_dir / "baseline_comparison.csv").exists()


def test_cli_without_input_preserves_the_demo_workflow(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "--simulations",
            "50",
            "--seed",
            "42",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert "Monte Carlo simulation completed." in capsys.readouterr().out
    assert (tmp_path / "triangular_histogram.png").exists()
