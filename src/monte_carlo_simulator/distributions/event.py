"""Event-based distribution placeholder."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution


@dataclass(slots=True)
class EventDistribution(BaseDistribution):
    probability: float
    impact: float

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        raise NotImplementedError("Event distribution will be implemented in a future phase.")
