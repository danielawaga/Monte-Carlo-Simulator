"""Event-based distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class EventDistribution(BaseDistribution):
    """Bernoulli event: zero when absent, impact when it occurs."""

    probability: float
    impact: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.probability) or not np.isfinite(self.impact):
            raise ValidationError("Event parameters must be finite numbers.")
        if not 0 <= self.probability <= 1:
            raise ValidationError("Event probability must be in the interval [0, 1].")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        occurrences = rng.random(size=size) < self.probability
        return occurrences.astype(float) * self.impact
