"""Log-normal distribution placeholder."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution


@dataclass(slots=True)
class LogNormalDistribution(BaseDistribution):
    mean: float
    standard_deviation: float

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        raise NotImplementedError("Log-normal distribution will be implemented in a future phase.")
