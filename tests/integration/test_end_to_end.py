from monte_carlo_simulator.application.service import run_demo_simulation
from monte_carlo_simulator.models import SimulationConfig


def test_end_to_end_demo_simulation(tmp_path) -> None:
    config = SimulationConfig(number_of_simulations=10_000, random_seed=42)

    result, histogram_path = run_demo_simulation(config=config, output_dir=tmp_path)

    assert len(result.samples) == 10_000
    assert histogram_path.exists()
    assert histogram_path.name == "triangular_histogram.png"
