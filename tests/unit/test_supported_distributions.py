import numpy as np
import pytest

from monte_carlo_simulator.distributions import (
    EventDistribution,
    LogNormalDistribution,
    NormalDistribution,
    PertDistribution,
    UniformDistribution,
)
from monte_carlo_simulator.engine import MonteCarloSimulator
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem, SimulationConfig


def test_pert_samples_are_bounded_and_match_theoretical_mean() -> None:
    rng = np.random.default_rng(42)
    distribution = PertDistribution(
        minimum=10.0,
        most_likely=20.0,
        maximum=40.0,
        lambda_shape=4.0,
    )

    samples = distribution.sample(rng, size=100_000)
    expected_mean = (10.0 + 4.0 * 20.0 + 40.0) / 6.0

    assert float(samples.min()) >= 10.0
    assert float(samples.max()) <= 40.0
    assert float(samples.mean()) == pytest.approx(expected_mean, rel=0.01)


def test_normal_matches_requested_moments() -> None:
    rng = np.random.default_rng(42)
    distribution = NormalDistribution(mean=100.0, standard_deviation=15.0)

    samples = distribution.sample(rng, size=100_000)

    assert float(samples.mean()) == pytest.approx(100.0, rel=0.01)
    assert float(samples.std()) == pytest.approx(15.0, rel=0.02)


def test_lognormal_uses_arithmetic_mean_and_standard_deviation() -> None:
    rng = np.random.default_rng(42)
    distribution = LogNormalDistribution(mean=100.0, standard_deviation=25.0)

    samples = distribution.sample(rng, size=150_000)

    assert np.all(samples > 0)
    assert float(samples.mean()) == pytest.approx(100.0, rel=0.015)
    assert float(samples.std()) == pytest.approx(25.0, rel=0.03)


def test_uniform_samples_stay_within_bounds() -> None:
    rng = np.random.default_rng(42)
    distribution = UniformDistribution(minimum=-5.0, maximum=15.0)

    samples = distribution.sample(rng, size=50_000)

    assert float(samples.min()) >= -5.0
    assert float(samples.max()) <= 15.0
    assert float(samples.mean()) == pytest.approx(5.0, abs=0.1)


def test_event_distribution_matches_probability_and_impact() -> None:
    rng = np.random.default_rng(42)
    distribution = EventDistribution(probability=0.25, impact=40_000.0)

    samples = distribution.sample(rng, size=100_000)

    assert set(np.unique(samples)).issubset({0.0, 40_000.0})
    observed_probability = float(np.mean(samples > 0))
    assert observed_probability == pytest.approx(0.25, abs=0.005)


def test_simulator_accepts_all_six_supported_distributions() -> None:
    items = [
        RiskItem("Triangular", "triangular", minimum=10, most_likely=20, maximum=30),
        RiskItem("PERT", "pert", minimum=10, most_likely=20, maximum=40),
        RiskItem("Uniform", "uniform", minimum=5, maximum=15),
        RiskItem("Normal", "normal", mean=50, standard_deviation=5),
        RiskItem("Log-normal", "log-normal", mean=30, standard_deviation=6),
        RiskItem("Event", "event", probability=0.2, impact=100),
    ]
    config = SimulationConfig(number_of_simulations=10_000, random_seed=42)

    result = MonteCarloSimulator().run(items, config)

    assert result.item_samples is not None
    assert result.item_samples.shape == (10_000, 6)
    assert result.samples.shape == (10_000,)
    assert set(result.item_samples.columns) == {item.name for item in items}


def test_invalid_distribution_parameters_are_rejected() -> None:
    with pytest.raises(ValidationError):
        RiskItem("Invalid normal", "normal", mean=100, standard_deviation=-1)

    with pytest.raises(ValidationError):
        RiskItem("Invalid event", "event", probability=1.2, impact=100)


def test_duplicate_item_names_are_rejected() -> None:
    items = [
        RiskItem("Duplicate", "uniform", minimum=0, maximum=1),
        RiskItem("Duplicate", "event", probability=0.1, impact=10),
    ]

    with pytest.raises(ValidationError, match="unique"):
        MonteCarloSimulator().run(items, SimulationConfig(number_of_simulations=100))
