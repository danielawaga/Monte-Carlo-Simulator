"""Normal distribution implementation."""

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy.stats import norm

from monte_carlo_simulator.distributions.base import (
    BaseDistribution,
    _as_finite_float,
    _validate_probabilities,
    _validated_sample_size,
)
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class NormalDistribution(BaseDistribution):
    """Normal distribution parameterized by arithmetic mean and standard deviation."""

    mean: float
    standard_deviation: float

    def __post_init__(self) -> None:
        self.mean = _as_finite_float(self.mean, "mean")
        self.standard_deviation = _as_finite_float(self.standard_deviation, "standard_deviation")
        if self.standard_deviation < 0:
            raise ValidationError("Normal standard_deviation must be non-negative.")

    def ppf(self, probabilities: object) -> np.ndarray:
        probabilities = _validate_probabilities(probabilities)
        if self.standard_deviation == 0:
            return np.full(probabilities.shape, self.mean, dtype=float)
        return cast(
            np.ndarray,
            norm.ppf(probabilities, loc=self.mean, scale=self.standard_deviation),
        )

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        size = _validated_sample_size(size)
        if self.standard_deviation == 0:
            return np.full(size, self.mean, dtype=float)
        return rng.normal(self.mean, self.standard_deviation, size=size)
