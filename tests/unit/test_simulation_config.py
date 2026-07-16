import math

import numpy as np
import pytest

from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import SimulationConfig


@pytest.mark.parametrize(
    "invalid_count",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(1.0, id="float"),
        pytest.param(True, id="boolean"),
        pytest.param("100", id="string"),
        pytest.param(None, id="none"),
        pytest.param(math.nan, id="nan"),
        pytest.param(math.inf, id="infinite"),
    ],
)
def test_invalid_numbers_of_simulations_are_rejected(invalid_count: object) -> None:
    with pytest.raises(ValidationError, match="strictly positive integer"):
        SimulationConfig(number_of_simulations=invalid_count)  # type: ignore[arg-type]


def test_numpy_integer_simulation_count_is_accepted_and_normalized() -> None:
    config = SimulationConfig(number_of_simulations=np.int64(25))  # type: ignore[arg-type]

    assert config.number_of_simulations == 25
    assert isinstance(config.number_of_simulations, int)


@pytest.mark.parametrize(
    "invalid_seed",
    [
        pytest.param(-1, id="negative"),
        pytest.param(1.0, id="float"),
        pytest.param(True, id="boolean"),
        pytest.param("1", id="string"),
    ],
)
def test_invalid_random_seeds_are_rejected(invalid_seed: object) -> None:
    with pytest.raises(ValidationError, match="random_seed"):
        SimulationConfig(random_seed=invalid_seed)  # type: ignore[arg-type]


def test_none_seed_is_supported_for_nondeterministic_runs() -> None:
    config = SimulationConfig(random_seed=None)

    assert config.random_seed is None


@pytest.mark.parametrize(
    "invalid_levels",
    [
        pytest.param((), id="empty"),
        pytest.param([0.5], id="not-a-tuple"),
        pytest.param((0,), id="zero"),
        pytest.param((1,), id="one"),
        pytest.param((-0.1,), id="negative"),
        pytest.param((1.1,), id="above-one"),
        pytest.param((math.nan,), id="nan"),
        pytest.param((math.inf,), id="infinite"),
        pytest.param((True,), id="boolean"),
        pytest.param(("0.5",), id="string"),
    ],
)
def test_invalid_confidence_levels_are_rejected(invalid_levels: object) -> None:
    with pytest.raises(ValidationError, match="confidence_levels"):
        SimulationConfig(confidence_levels=invalid_levels)  # type: ignore[arg-type]


def test_confidence_levels_are_normalized_to_python_floats() -> None:
    config = SimulationConfig(confidence_levels=(np.float64(0.5), np.float64(0.9)))

    assert config.confidence_levels == (0.5, 0.9)
    assert all(isinstance(level, float) for level in config.confidence_levels)
