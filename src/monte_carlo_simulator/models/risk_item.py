"""Data model for a project risk line."""

from dataclasses import dataclass

from monte_carlo_simulator.exceptions import ValidationError


@dataclass(slots=True)
class RiskItem:
    name: str
    distribution: str
    minimum: float | None = None
    most_likely: float | None = None
    maximum: float | None = None
    mean: float | None = None
    standard_deviation: float | None = None
    probability: float | None = None
    impact: float | None = None
    category: str | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        if self.distribution == "triangular":
            self._validate_triangular_parameters()

    def _validate_triangular_parameters(self) -> None:
        if self.minimum is None or self.most_likely is None or self.maximum is None:
            raise ValidationError(
                f"Risk item '{self.name}' requires minimum, most_likely and "
                "maximum for triangular distribution."
            )
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError(
                f"Invalid triangular parameters for '{self.name}': "
                "minimum <= most_likely <= maximum must hold."
            )
