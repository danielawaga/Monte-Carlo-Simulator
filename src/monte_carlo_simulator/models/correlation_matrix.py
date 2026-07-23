"""Validated item correlation matrix."""

from dataclasses import dataclass
from numbers import Real

import numpy as np

from monte_carlo_simulator.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class CorrelationMatrix:
    """Correlation matrix aligned to active risk item names."""

    item_names: tuple[str, ...]
    values: np.ndarray

    def __init__(self, item_names: list[str] | tuple[str, ...], values: object) -> None:
        names = tuple(item_names)
        if not names:
            raise ValidationError("Correlation matrix requires at least one item name.")
        if len({name.casefold() for name in names}) != len(names):
            raise ValidationError("Correlation matrix item names must be unique.")
        array = np.asarray(values, dtype=float)
        if array.shape != (len(names), len(names)):
            raise ValidationError(
                "Correlation matrix must be square and match the number of active items."
            )
        if not np.all(np.isfinite(array)):
            raise ValidationError("Correlation matrix coefficients must be finite real numbers.")
        if not np.all((array >= -1.0) & (array <= 1.0)):
            raise ValidationError("Correlation coefficients must be in [-1, 1].")
        if not np.allclose(np.diag(array), 1.0):
            raise ValidationError("Correlation matrix diagonal coefficients must all be 1.")
        if not np.allclose(array, array.T, atol=1e-10):
            raise ValidationError("Correlation matrix must be symmetric.")
        try:
            np.linalg.cholesky(array)
        except np.linalg.LinAlgError as exc:
            raise ValidationError("Correlation matrix must be strictly positive definite.") from exc
        object.__setattr__(self, "item_names", names)
        object.__setattr__(self, "values", array)


def as_correlation_value(value: object, field: str = "correlation coefficient") -> float:
    """Validate one worksheet correlation coefficient."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f"{field} must be a finite real number in [-1, 1].")
    coefficient = float(value)
    if not np.isfinite(coefficient) or not -1 <= coefficient <= 1:
        raise ValidationError(f"{field} must be a finite real number in [-1, 1].")
    return coefficient
