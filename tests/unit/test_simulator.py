import numpy as np

from monte_carlo_simulator.engine import MonteCarloSimulator
from monte_carlo_simulator.models import SimulationConfig


def test_reproducible_results_with_same_seed(sample_items) -> None:
    simulator = MonteCarloSimulator()
    config = SimulationConfig(number_of_simulations=10_000, random_seed=123)
    run_1 = simulator.run(sample_items, config)
    run_2 = simulator.run(sample_items, config)

    assert np.allclose(run_1.samples, run_2.samples)


def test_simulator_produces_expected_number_of_total_costs(sample_items) -> None:
    simulator = MonteCarloSimulator()
    config = SimulationConfig(number_of_simulations=10_000, random_seed=123)

    result = simulator.run(sample_items, config)

    assert len(result.samples) == 10_000
