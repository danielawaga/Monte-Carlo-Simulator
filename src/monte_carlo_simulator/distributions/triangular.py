"""Triangular distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class TriangularDistribution(BaseDistribution):
    minimum: float
    most_likely: float
    maximum: float

    def __post_init__(self) -> None:
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError(
                "Triangular parameters must satisfy minimum <= most_likely <= maximum."
            )

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        return rng.triangular(self.minimum, self.most_likely, self.maximum, size=size)
