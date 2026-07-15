import pytest

from monte_carlo_simulator.models import RiskItem, SimulationConfig


@pytest.fixture
def sample_items() -> list[RiskItem]:
    return [
        RiskItem("A", "triangular", minimum=1.0, most_likely=2.0, maximum=4.0),
        RiskItem("B", "triangular", minimum=2.0, most_likely=3.0, maximum=5.0),
        RiskItem("C", "triangular", minimum=3.0, most_likely=4.0, maximum=7.0),
        RiskItem("D", "triangular", minimum=1.0, most_likely=2.0, maximum=3.0),
        RiskItem("E", "triangular", minimum=2.0, most_likely=2.5, maximum=3.0),
    ]


@pytest.fixture
def sample_config() -> SimulationConfig:
    return SimulationConfig(number_of_simulations=10_000, random_seed=42)
