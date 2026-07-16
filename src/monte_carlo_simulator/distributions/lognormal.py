"""Log-normal distribution implementation."""

from dataclasses import dataclass
from math import log, sqrt

import numpy as np

from monte_carlo_simulator.distributions.base import (
    BaseDistribution,
    _as_finite_float,
    _validated_sample_size,
)
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class LogNormalDistribution(BaseDistribution):
    """Log-normal distribution using arithmetic-space mean and standard deviation."""

    mean: float
    standard_deviation: float

    def __post_init__(self) -> None:
        self.mean = _as_finite_float(self.mean, "mean")
        self.standard_deviation = _as_finite_float(self.standard_deviation, "standard_deviation")
        if self.mean <= 0:
            raise ValidationError("Log-normal mean must be strictly positive.")
        if self.standard_deviation < 0:
            raise ValidationError("Log-normal standard_deviation must be non-negative.")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        size = _validated_sample_size(size)
        if self.standard_deviation == 0:
            return np.full(size, self.mean, dtype=float)

        log_mean, log_sigma = self._log_space_parameters()
        return rng.lognormal(mean=log_mean, sigma=log_sigma, size=size)

    def _log_space_parameters(self) -> tuple[float, float]:
        """Convert arithmetic moments to log-space without ratio overflow."""
        arithmetic_log_mean = log(self.mean)
        arithmetic_log_standard_deviation = log(self.standard_deviation)
        sigma_squared = float(
            np.logaddexp(
                2.0 * arithmetic_log_mean,
                2.0 * arithmetic_log_standard_deviation,
            )
            - 2.0 * arithmetic_log_mean
        )
        log_sigma = sqrt(max(sigma_squared, 0.0))
        log_mean = arithmetic_log_mean - 0.5 * sigma_squared
        return log_mean, log_sigma
