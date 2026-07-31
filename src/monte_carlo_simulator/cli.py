"""Command-line entrypoint for Excel and demonstration simulations."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from monte_carlo_simulator.application.service import (
    run_demo_simulation,
    run_simulation_from_excel,
)
from monte_carlo_simulator.exceptions import MonteCarloError
from monte_carlo_simulator.models import SimulationConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Monte Carlo simulation from a schema-v1 Excel risk register."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to a schema-v1 .xlsx risk register; omit to run the built-in demo",
    )
    parser.add_argument(
        "--simulations", type=int, default=10_000, help="Number of Monte Carlo draws"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible runs")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where output artifacts are saved (default: data/output)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = SimulationConfig(number_of_simulations=args.simulations, random_seed=args.seed)
        if args.input is None:
            result, histogram_path = run_demo_simulation(
                config=config,
                output_dir=args.output_dir,
            )
            artifact_lines = [f"Histogram saved to: {histogram_path}"]
        else:
            run = run_simulation_from_excel(
                args.input,
                config=config,
                output_dir=args.output_dir,
            )
            result = run.result
            artifact_lines = [
                f"Project: {run.metadata.project_name}",
                f"Analysis: {run.metadata.analysis_type} ({run.metadata.default_unit})",
                f"Histogram saved to: {run.histogram_path}",
                f"Summary saved to: {run.summary_path}",
                f"S-curve saved to: {run.s_curve_path}",
                f"Percentile table saved to: {run.percentile_table_path}",
                f"Convergence diagnostics saved to: {run.convergence_path}",
                f"Sensitivity saved to: {run.sensitivity_path}",
                f"Tornado chart saved to: {run.tornado_path}",
            ]
            if run.correlation_diagnostics_path is not None:
                artifact_lines.append(
                    "Correlation diagnostics saved to: "
                    f"{run.correlation_diagnostics_path}"
                )
            if run.baseline_comparison_path is not None:
                artifact_lines.append(
                    f"Baseline comparison saved to: {run.baseline_comparison_path}"
                )
    except MonteCarloError as exc:
        parser.error(str(exc))

    print("Monte Carlo simulation completed.")
    print("Summary statistics:")
    print(result.summary.to_string(index=False))
    for line in artifact_lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
