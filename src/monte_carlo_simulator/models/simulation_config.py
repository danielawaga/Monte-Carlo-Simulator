"""Simulation configuration model."""

from dataclasses import dataclass
from math import isfinite
from numbers import Integral, Real

from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class SimulationConfig:
    number_of_simulations: int = 10_000
    random_seed: int | None = 42
    confidence_levels: tuple[float, ...] = (0.50, 0.80, 0.90)

    def __post_init__(self) -> None:
        if (
            isinstance(self.number_of_simulations, bool)
            or not isinstance(self.number_of_simulations, Integral)
            or self.number_of_simulations <= 0
        ):
            raise ValidationError("number_of_simulations must be a strictly positive integer.")
        self.number_of_simulations = int(self.number_of_simulations)

        if self.random_seed is not None:
            if (
                isinstance(self.random_seed, bool)
                or not isinstance(self.random_seed, Integral)
                or self.random_seed < 0
            ):
                raise ValidationError("random_seed must be a non-negative integer or None.")
            self.random_seed = int(self.random_seed)

        if not isinstance(self.confidence_levels, tuple) or not self.confidence_levels:
            raise ValidationError("confidence_levels must be a non-empty tuple.")

        normalized_levels: list[float] = []
        for level in self.confidence_levels:
            if (
                isinstance(level, bool)
                or not isinstance(level, Real)
                or not isfinite(float(level))
                or not 0 < level < 1
            ):
                raise ValidationError("confidence_levels must be finite values in (0, 1).")
            normalized_levels.append(float(level))
        self.confidence_levels = tuple(normalized_levels)
