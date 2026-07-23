"""Uniform distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import (
    BaseDistribution,
    _as_finite_float,
    _validate_probabilities,
    _validated_sample_size,
)
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class UniformDistribution(BaseDistribution):
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        self.minimum = _as_finite_float(self.minimum, "minimum")
        self.maximum = _as_finite_float(self.maximum, "maximum")
        if self.minimum > self.maximum:
            raise ValidationError("Uniform parameters must satisfy minimum <= maximum.")

    def ppf(self, probabilities: object) -> np.ndarray:
        probabilities = _validate_probabilities(probabilities)
        if self.minimum == self.maximum:
            return np.full(probabilities.shape, self.minimum, dtype=float)
        return (1.0 - probabilities) * self.minimum + probabilities * self.maximum

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        size = _validated_sample_size(size)
        if self.minimum == self.maximum:
            return np.full(size, self.minimum, dtype=float)
        unit_samples = rng.random(size=size)
        return (1.0 - unit_samples) * self.minimum + unit_samples * self.maximum
