import math

import numpy as np
import pytest

import monte_carlo_simulator.engine.simulator as simulator_module
from monte_carlo_simulator.engine import MonteCarloSimulator
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem, SimulationConfig


def _mixed_items() -> list[RiskItem]:
    return [
        RiskItem("Triangular", "triangular", minimum=10, most_likely=20, maximum=30),
        RiskItem(
            "PERT",
            "beta-pert",
            minimum=10,
            most_likely=20,
            maximum=40,
            lambda_shape=8,
        ),
        RiskItem("Uniform", "uniform", minimum=5, maximum=15),
        RiskItem("Normal", "normal", mean=50, standard_deviation=5),
        RiskItem("Log-normal", "log-normal", mean=30, standard_deviation=6),
        RiskItem("Event", "bernoulli", probability=0.2, impact=-100),
    ]


def test_simulator_mixes_all_six_distributions_with_expected_mean() -> None:
    sample_size = 100_000
    items = _mixed_items()
    result = MonteCarloSimulator().run(
        items,
        SimulationConfig(number_of_simulations=sample_size, random_seed=42),
    )
    triangular_variance = (10**2 + 20**2 + 30**2 - 10 * 20 - 10 * 30 - 20 * 30) / 18
    pert_variance = 30**2 * (11 / 3) * (19 / 3) / (10**2 * 11)
    uniform_variance = 10**2 / 12
    aggregate_variance = (
        triangular_variance + pert_variance + uniform_variance + 5**2 + 6**2 + 100**2 * 0.2 * 0.8
    )
    expected_mean = 20 + 21 + 10 + 50 + 30 - 20
    statistical_tolerance = 6 * math.sqrt(aggregate_variance / sample_size)

    assert result.samples.shape == (sample_size,)
    assert result.item_samples is not None
    assert result.item_samples.shape == (sample_size, 6)
    assert list(result.item_samples.columns) == [item.name for item in items]
    assert np.array_equal(result.samples, result.item_samples.sum(axis=1).to_numpy())
    assert float(result.samples.mean()) == pytest.approx(
        expected_mean,
        abs=statistical_tolerance,
    )


def test_simulator_is_exactly_reproducible_with_same_seed() -> None:
    simulator = MonteCarloSimulator()
    config = SimulationConfig(number_of_simulations=2_000, random_seed=123)

    first = simulator.run(_mixed_items(), config)
    second = simulator.run(_mixed_items(), config)

    assert np.array_equal(first.samples, second.samples)
    assert first.item_samples is not None
    assert second.item_samples is not None
    assert first.item_samples.equals(second.item_samples)


def test_different_seeds_change_stochastic_samples() -> None:
    simulator = MonteCarloSimulator()

    first = simulator.run(
        _mixed_items(),
        SimulationConfig(number_of_simulations=1_000, random_seed=1),
    )
    second = simulator.run(
        _mixed_items(),
        SimulationConfig(number_of_simulations=1_000, random_seed=2),
    )

    assert not np.array_equal(first.samples, second.samples)


def test_simulator_rejects_an_empty_risk_register() -> None:
    with pytest.raises(ValidationError, match="At least one"):
        MonteCarloSimulator().run([], SimulationConfig(number_of_simulations=10))


@pytest.mark.parametrize(
    ("first_name", "second_name"),
    [
        pytest.param("Duplicate", "Duplicate", id="exact"),
        pytest.param("Duplicate", " duplicate ", id="trimmed-and-case-insensitive"),
    ],
)
def test_duplicate_item_names_are_rejected(
    first_name: str,
    second_name: str,
) -> None:
    items = [
        RiskItem(first_name, "uniform", minimum=0, maximum=1),
        RiskItem(second_name, "event", probability=0.1, impact=10),
    ]

    with pytest.raises(ValidationError, match="unique"):
        MonteCarloSimulator().run(items, SimulationConfig(number_of_simulations=100))


def test_engine_requests_one_vector_per_item_instead_of_one_draw_at_a_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_calls: list[tuple[np.random.Generator, int]] = []

    class RecordingDistribution:
        def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
            sample_calls.append((rng, size))
            return np.ones(size, dtype=float)

    monkeypatch.setattr(
        simulator_module,
        "build_distribution",
        lambda _item: RecordingDistribution(),
    )
    items = [
        RiskItem("A", "uniform", minimum=0, maximum=1),
        RiskItem("B", "uniform", minimum=0, maximum=1),
        RiskItem("C", "uniform", minimum=0, maximum=1),
    ]

    result = MonteCarloSimulator().run(
        items,
        SimulationConfig(number_of_simulations=2_500, random_seed=7),
    )

    assert [size for _rng, size in sample_calls] == [2_500, 2_500, 2_500]
    assert len({id(rng) for rng, _size in sample_calls}) == 1
    assert np.array_equal(result.samples, np.full(2_500, 3.0))
