"""Data model for a project risk line."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

from monte_carlo_simulator.exceptions import ValidationError

_DISTRIBUTION_ALIASES = {
    "beta pert": "pert",
    "beta-pert": "pert",
    "beta_pert": "pert",
    "bernoulli": "event",
    "bernoulli-event": "event",
    "bernoulli_event": "event",
    "event based": "event",
    "event-based": "event",
    "event_based": "event",
    "eventual": "event",
    "log normal": "lognormal",
    "log-normal": "lognormal",
    "log_normal": "lognormal",
}
SUPPORTED_DISTRIBUTIONS = frozenset(
    {
        "triangular",
        "pert",
        "uniform",
        "normal",
        "lognormal",
        "event",
    }
)


def normalize_distribution_name(distribution: str) -> str:
    """Normalize a supported distribution name or alias to its canonical name."""
    normalized = distribution.strip().casefold()
    return _DISTRIBUTION_ALIASES.get(normalized, normalized)


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
    lambda_shape: float = 4.0
    notes: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise ValidationError("Risk item name must be a string.")
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("Risk item name must not be empty.")

        if not isinstance(self.distribution, str):
            raise ValidationError("Risk item distribution must be a string.")
        self.distribution = normalize_distribution_name(self.distribution)
        if self.distribution not in SUPPORTED_DISTRIBUTIONS:
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

        self.minimum = _as_finite_float(self.minimum, "minimum", self.name)
        self.most_likely = _as_finite_float(self.most_likely, "most_likely", self.name)
        self.maximum = _as_finite_float(self.maximum, "maximum", self.name)
        if not (self.minimum <= self.most_likely <= self.maximum):
            raise ValidationError(
                f"Invalid {self.distribution} parameters for '{self.name}': "
                "minimum <= most_likely <= maximum must hold."
            )
        if self.distribution == "pert":
            self.lambda_shape = _as_finite_float(self.lambda_shape, "lambda_shape", self.name)
            if self.lambda_shape <= 0:
                raise ValidationError(
                    f"lambda_shape must be strictly positive for PERT risk item '{self.name}'."
                )

    def _validate_uniform_parameters(self) -> None:
        if self.minimum is None or self.maximum is None:
            raise ValidationError(
                f"Risk item '{self.name}' requires minimum and maximum for uniform distribution."
            )

        self.minimum = _as_finite_float(self.minimum, "minimum", self.name)
        self.maximum = _as_finite_float(self.maximum, "maximum", self.name)
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

        self.mean = _as_finite_float(self.mean, "mean", self.name)
        self.standard_deviation = _as_finite_float(
            self.standard_deviation, "standard_deviation", self.name
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
                f"Risk item '{self.name}' requires probability and impact for event distribution."
            )

        self.probability = _as_finite_float(self.probability, "probability", self.name)
        self.impact = _as_finite_float(self.impact, "impact", self.name)
        if not 0 <= self.probability <= 1:
            raise ValidationError(
                f"probability must be in [0, 1] for event risk item '{self.name}'."
            )


def _as_finite_float(value: object, parameter_name: str, item_name: str) -> float:
    """Return a risk-item parameter as a finite Python float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(
            f"{parameter_name} must be a finite real number for risk item '{item_name}'."
        )

    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise ValidationError(
            f"{parameter_name} must be a finite real number for risk item '{item_name}'."
        )
    return numeric_value
