"""Data model for a project risk line."""

from dataclasses import dataclass

from monte_carlo_simulator.exceptions import ValidationError

_DISTRIBUTION_ALIASES = {
    "log-normal": "lognormal",
    "log_normal": "lognormal",
    "event-based": "event",
    "event_based": "event",
    "eventual": "event",
}
_SUPPORTED_DISTRIBUTIONS = {
    "triangular",
    "pert",
    "uniform",
    "normal",
    "lognormal",
    "event",
}


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
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("Risk item name must not be empty.")

        raw_distribution = self.distribution.strip().lower()
        self.distribution = _DISTRIBUTION_ALIASES.get(raw_distribution, raw_distribution)
        if self.distribution not in _SUPPORTED_DISTRIBUTIONS:
            raise ValidationError(
                f"Unsupported distribution '{self.distribution}' for risk item '{self.name}'."
            )

        if self.distribution in {"triangular", "pert"}:
            self._validate_three_point_parameters()
        elif self.distribution == "uniform":
            self._validate_uniform_parameters()
        elif self.distribution in {"normal", "lognormal"}:
            self._validate_moment_parameters()
        elif self.distribution == "event":
            self._validate_event_parameters()

    def _validate_three_point_parameters(self) -> None:
        if self.minimum is None or self.most_likely is None or self.maximum is None:
            raise ValidationError(
                f"Risk item '{self.name}' requires minimum, most_likely and maximum "
                f"for {self.distribution} distribution."
            )
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError(
                f"Invalid {self.distribution} parameters for '{self.name}': "
                "minimum <= most_likely <= maximum must hold."
            )

    def _validate_uniform_parameters(self) -> None:
        if self.minimum is None or self.maximum is None:
            raise ValidationError(
                f"Risk item '{self.name}' requires minimum and maximum "
                "for uniform distribution."
            )
        if self.minimum > self.maximum:
            raise ValidationError(
                f"Invalid uniform parameters for '{self.name}': minimum <= maximum must hold."
            )

    def _validate_moment_parameters(self) -> None:
        if self.mean is None or self.standard_deviation is None:
            raise ValidationError(
                f"Risk item '{self.name}' requires mean and standard_deviation "
                f"for {self.distribution} distribution."
            )
        if self.standard_deviation < 0:
            raise ValidationError(
                f"standard_deviation must be non-negative for risk item '{self.name}'."
            )
        if self.distribution == "lognormal" and self.mean <= 0:
            raise ValidationError(
                f"mean must be strictly positive for lognormal risk item '{self.name}'."
            )

    def _validate_event_parameters(self) -> None:
        if self.probability is None or self.impact is None:
            raise ValidationError(
                f"Risk item '{self.name}' requires probability and impact "
                "for event distribution."
            )
        if not 0 <= self.probability <= 1:
            raise ValidationError(
                f"probability must be in [0, 1] for event risk item '{self.name}'."
            )
