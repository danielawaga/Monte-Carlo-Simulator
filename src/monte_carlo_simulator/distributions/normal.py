"""Normal distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class NormalDistribution(BaseDistribution):
    """Normal distribution parameterized by arithmetic mean and standard deviation."""

    mean: float
    standard_deviation: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.mean) or not np.isfinite(self.standard_deviation):
            raise ValidationError("Normal parameters must be finite numbers.")
        if self.standard_deviation < 0:
            raise ValidationError("Normal standard_deviation must be non-negative.")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        if self.standard_deviation == 0:
            return np.full(size, self.mean, dtype=float)
        return rng.normal(self.mean, self.standard_deviation, size=size)
