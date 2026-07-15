"""CLI entrypoint for the week-1 Monte Carlo proof of concept."""

import argparse
from pathlib import Path

from monte_carlo_simulator.application.service import run_demo_simulation
from monte_carlo_simulator.models import SimulationConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Monte Carlo triangular demo simulation.")
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


def main() -> None:
    args = build_parser().parse_args()
    config = SimulationConfig(number_of_simulations=args.simulations, random_seed=args.seed)
    result, histogram_path = run_demo_simulation(config=config, output_dir=args.output_dir)

    print("Monte Carlo simulation completed.")
    print("Summary statistics:")
    print(result.summary.to_string(index=False))
    print(f"Histogram saved to: {histogram_path}")


if __name__ == "__main__":
    main()
