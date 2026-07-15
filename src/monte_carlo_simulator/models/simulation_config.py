"""Simulation configuration model."""

from dataclasses import dataclass

from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class SimulationConfig:
    number_of_simulations: int = 10_000
    random_seed: int | None = 42
    confidence_levels: tuple[float, ...] = (0.50, 0.80, 0.90)

    def __post_init__(self) -> None:
        if self.number_of_simulations <= 0:
            raise ValidationError("number_of_simulations must be strictly positive.")
        if any(level <= 0 or level >= 1 for level in self.confidence_levels):
            raise ValidationError("confidence_levels must be in the interval (0, 1).")
