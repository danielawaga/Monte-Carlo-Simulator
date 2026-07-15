"""PERT distribution placeholder."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution


@dataclass(slots=True)
class PertDistribution(BaseDistribution):
    minimum: float
    most_likely: float
    maximum: float
    lambda_shape: float = 4.0

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        raise NotImplementedError("PERT distribution will be implemented in a future phase.")
