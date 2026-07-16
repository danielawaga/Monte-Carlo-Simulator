"""Uniform distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class UniformDistribution(BaseDistribution):
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.minimum) or not np.isfinite(self.maximum):
            raise ValidationError("Uniform parameters must be finite numbers.")
        if self.minimum > self.maximum:
            raise ValidationError("Uniform parameters must satisfy minimum <= maximum.")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        if self.minimum == self.maximum:
            return np.full(size, self.minimum, dtype=float)
        return rng.uniform(self.minimum, self.maximum, size=size)
