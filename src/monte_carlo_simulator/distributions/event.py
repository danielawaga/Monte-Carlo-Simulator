"""Event-based distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import (
    BaseDistribution,
    _as_finite_float,
    _validated_sample_size,
)
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class EventDistribution(BaseDistribution):
    """Bernoulli event: zero when absent, impact when it occurs."""

    probability: float
    impact: float

    def __post_init__(self) -> None:
        self.probability = _as_finite_float(self.probability, "probability")
        self.impact = _as_finite_float(self.impact, "impact")
        if not 0 <= self.probability <= 1:
            raise ValidationError("Event probability must be in the interval [0, 1].")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        size = _validated_sample_size(size)
        if self.probability == 0 or self.impact == 0:
            return np.zeros(size, dtype=float)
        if self.probability == 1:
            return np.full(size, self.impact, dtype=float)

        occurrences = rng.random(size=size) < self.probability
        return np.where(occurrences, self.impact, 0.0)
