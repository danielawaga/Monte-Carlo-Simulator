"""Log-normal distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class LogNormalDistribution(BaseDistribution):
    """Log-normal distribution using arithmetic-space mean and standard deviation."""

    mean: float
    standard_deviation: float

    def __post_init__(self) -> None:
        if not np.isfinite(self.mean) or not np.isfinite(self.standard_deviation):
            raise ValidationError("Log-normal parameters must be finite numbers.")
        if self.mean <= 0:
            raise ValidationError("Log-normal mean must be strictly positive.")
        if self.standard_deviation < 0:
            raise ValidationError("Log-normal standard_deviation must be non-negative.")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        if self.standard_deviation == 0:
            return np.full(size, self.mean, dtype=float)

        sigma_squared = np.log1p((self.standard_deviation / self.mean) ** 2)
        log_sigma = float(np.sqrt(sigma_squared))
        log_mean = float(np.log(self.mean) - 0.5 * sigma_squared)
        return rng.lognormal(mean=log_mean, sigma=log_sigma, size=size)
