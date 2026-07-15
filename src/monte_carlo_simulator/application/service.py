"""Application service orchestration."""

from pathlib import Path

from monte_carlo_simulator.config import OUTPUT_DIR
from monte_carlo_simulator.engine import MonteCarloSimulator
from monte_carlo_simulator.models import RiskItem, SimulationConfig, SimulationResult
from monte_carlo_simulator.visualization.histogram import save_histogram


def create_sample_risk_items() -> list[RiskItem]:
    """Create five fictive triangular risk items."""
    return [
        RiskItem(
            "Studies",
            "triangular",
            minimum=10_000,
            most_likely=15_000,
            maximum=22_000,
            category="engineering",
            unit="EUR",
        ),
        RiskItem(
            "Development",
            "triangular",
            minimum=30_000,
            most_likely=45_000,
            maximum=70_000,
            category="engineering",
            unit="EUR",
        ),
        RiskItem(
            "Testing",
            "triangular",
            minimum=12_000,
            most_likely=20_000,
            maximum=32_000,
            category="quality",
            unit="EUR",
        ),
        RiskItem(
            "Documentation",
            "triangular",
            minimum=4_000,
            most_likely=7_000,
            maximum=12_000,
            category="management",
            unit="EUR",
        ),
        RiskItem(
            "Deployment",
            "triangular",
            minimum=8_000,
            most_likely=13_000,
            maximum=21_000,
            category="operations",
            unit="EUR",
        ),
    ]


def run_demo_simulation(
    config: SimulationConfig | None = None,
    output_dir: Path | None = None,
) -> tuple[SimulationResult, Path]:
    """Run the week-1 triangular proof of concept and save histogram."""
    simulation_config = config or SimulationConfig()
    simulator = MonteCarloSimulator()
    result = simulator.run(create_sample_risk_items(), simulation_config)

    target_dir = output_dir or OUTPUT_DIR
    histogram_path = target_dir / "triangular_histogram.png"
    save_histogram(result.samples, result.summary, histogram_path)
    return result, histogram_path
