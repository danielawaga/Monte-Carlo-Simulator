"""Beta-PERT distribution implementation."""

from dataclasses import dataclass

import numpy as np

from monte_carlo_simulator.distributions.base import (
    BaseDistribution,
    _as_finite_float,
    _scaled_interval_position,
    _validated_sample_size,
)
from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class PertDistribution(BaseDistribution):
    """Bounded PERT distribution parameterized by min, mode and max."""

    minimum: float
    most_likely: float
    maximum: float
    lambda_shape: float = 4.0

    def __post_init__(self) -> None:
        self.minimum = _as_finite_float(self.minimum, "minimum")
        self.most_likely = _as_finite_float(self.most_likely, "most_likely")
        self.maximum = _as_finite_float(self.maximum, "maximum")
        self.lambda_shape = _as_finite_float(self.lambda_shape, "lambda_shape")
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError("PERT parameters must satisfy minimum <= most_likely <= maximum.")
        if self.lambda_shape <= 0:
            raise ValidationError("PERT lambda_shape must be strictly positive.")

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        size = _validated_sample_size(size)
        if self.minimum == self.maximum:
            return np.full(size, self.minimum, dtype=float)

        alpha, beta = self._shape_parameters()
        unit_samples = rng.beta(alpha, beta, size=size)
        return (1.0 - unit_samples) * self.minimum + unit_samples * self.maximum

    def _shape_parameters(self) -> tuple[float, float]:
        """Return the beta shapes while avoiding overflow in the interval width."""
        mode_position = _scaled_interval_position(
            self.minimum,
            self.most_likely,
            self.maximum,
        )
        alpha = 1.0 + self.lambda_shape * mode_position
        beta = 1.0 + self.lambda_shape * (1.0 - mode_position)
        return alpha, beta
