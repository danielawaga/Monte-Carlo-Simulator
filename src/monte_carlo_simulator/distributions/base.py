"""Distribution abstraction."""

from abc import ABC, abstractmethod
from math import isfinite
from numbers import Integral, Real

import numpy as np

from monte_carlo_simulator.exceptions import ValidationError


def _as_finite_float(value: object, parameter_name: str) -> float:
    """Return a real-valued parameter as a finite Python float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f"{parameter_name} must be a finite real number.")

    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise ValidationError(f"{parameter_name} must be a finite real number.")
    return numeric_value


def _validate_probabilities(probabilities: object) -> np.ndarray:
    """Validate probability inputs for inverse-CDF methods while preserving shape."""
    array = np.asarray(probabilities)
    if array.dtype == np.dtype(bool) or array.dtype.kind in {"b", "c", "O", "S", "U", "V"}:
        raise ValidationError("Probabilities must be finite real numbers in [0, 1].")
    try:
        numeric = array.astype(float, copy=False)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Probabilities must be finite real numbers in [0, 1].") from exc
    if not np.all(np.isfinite(numeric)) or not np.all((0.0 <= numeric) & (numeric <= 1.0)):
        raise ValidationError("Probabilities must be finite real numbers in [0, 1].")
    return numeric


def _validated_sample_size(size: object) -> int:
    """Validate the one-dimensional sample size accepted by all distributions."""
    if isinstance(size, bool) or not isinstance(size, Integral) or size <= 0:
        raise ValidationError("Sample size must be a strictly positive integer.")
    return int(size)


def _scaled_interval_position(minimum: float, value: float, maximum: float) -> float:
    """Locate a bounded value in [0, 1] without overflowing the interval width."""
    scale = max(abs(minimum), abs(value), abs(maximum), 1.0)
    scaled_minimum = minimum / scale
    scaled_value = value / scale
    scaled_maximum = maximum / scale
    position = (scaled_value - scaled_minimum) / (scaled_maximum - scaled_minimum)
    return min(max(position, 0.0), 1.0)


class BaseDistribution(ABC):
    """Defines the contract for all probability distributions."""

    @abstractmethod
    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        """Draw vectorized samples from the distribution."""
