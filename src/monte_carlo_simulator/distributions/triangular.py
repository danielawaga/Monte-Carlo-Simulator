"""Triangular distribution implementation."""

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
class TriangularDistribution(BaseDistribution):
    minimum: float
    most_likely: float
    maximum: float

    def __post_init__(self) -> None:
        self.minimum = _as_finite_float(self.minimum, "minimum")
        self.most_likely = _as_finite_float(self.most_likely, "most_likely")
        self.maximum = _as_finite_float(self.maximum, "maximum")
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError(
                "Triangular parameters must satisfy minimum <= most_likely <= maximum."
            )

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        size = _validated_sample_size(size)
        if self.minimum == self.maximum:
            return np.full(size, self.minimum, dtype=float)

        mode_position = _scaled_interval_position(
            self.minimum,
            self.most_likely,
            self.maximum,
        )
        probabilities = rng.random(size=size)
        unit_samples = np.where(
            probabilities < mode_position,
            np.sqrt(probabilities * mode_position),
            1.0 - np.sqrt((1.0 - probabilities) * (1.0 - mode_position)),
        )
        return (1.0 - unit_samples) * self.minimum + unit_samples * self.maximum
