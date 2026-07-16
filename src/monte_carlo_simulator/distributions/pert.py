"""Beta-PERT distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class PertDistribution(BaseDistribution):
    """Bounded PERT distribution parameterized by min, mode and max."""

    minimum: float
    most_likely: float
    maximum: float
    lambda_shape: float = 4.0

    def __post_init__(self) -> None:
        parameters = (self.minimum, self.most_likely, self.maximum, self.lambda_shape)
        if not all(np.isfinite(value) for value in parameters):
            raise ValidationError("PERT parameters must be finite numbers.")
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError(
                "PERT parameters must satisfy minimum <= most_likely <= maximum."
            )
        if self.lambda_shape <= 0:
            raise ValidationError("PERT lambda_shape must be strictly positive.")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        if self.minimum == self.maximum:
            return np.full(size, self.minimum, dtype=float)

        span = self.maximum - self.minimum
        alpha = 1.0 + self.lambda_shape * (self.most_likely - self.minimum) / span
        beta = 1.0 + self.lambda_shape * (self.maximum - self.most_likely) / span
        return self.minimum + span * rng.beta(alpha, beta, size=size)
