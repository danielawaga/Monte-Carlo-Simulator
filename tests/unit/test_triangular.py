import numpy as np
import pytest

from monte_carlo_simulator.distributions.triangular import TriangularDistribution
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem


def test_triangular_returns_expected_size() -> None:
    rng = np.random.default_rng(42)
    dist = TriangularDistribution(minimum=1.0, most_likely=2.0, maximum=4.0)

    samples = dist.sample(rng, size=10_000)

    assert len(samples) == 10_000


def test_triangular_samples_within_bounds() -> None:
    rng = np.random.default_rng(42)
    dist = TriangularDistribution(minimum=1.0, most_likely=2.0, maximum=4.0)

    samples = dist.sample(rng, size=10_000)

    assert float(samples.min()) >= 1.0
    assert float(samples.max()) <= 4.0


def test_invalid_triangular_configuration_raises_error() -> None:
    with pytest.raises(ValidationError):
        RiskItem(
            name="Invalid",
            distribution="triangular",
            minimum=3.0,
            most_likely=2.0,
            maximum=1.0,
        )
