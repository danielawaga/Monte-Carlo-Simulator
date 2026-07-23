"""Validated item correlation matrix."""

from dataclasses import dataclass
from numbers import Real

import numpy as np

from monte_carlo_simulator.exceptions import ValidationError

DIAGONAL_TOLERANCE = 1e-12
SYMMETRY_TOLERANCE = 1e-12


@dataclass(frozen=True, slots=True)
class CorrelationMatrix:
    """Correlation matrix aligned to active risk item names."""

    item_names: tuple[str, ...]
    values: np.ndarray

    def __init__(self, item_names: list[str] | tuple[str, ...], values: object) -> None:
        names = _validate_item_names(item_names)
        array = _validate_matrix_values(values, len(names))
        object.__setattr__(self, "item_names", names)
        object.__setattr__(self, "values", array)

    def aligned_to(self, item_names: list[str] | tuple[str, ...]) -> "CorrelationMatrix":
        """Return a copy aligned to the supplied item order."""
        target_names = _validate_item_names(item_names)
        current = {name.casefold(): index for index, name in enumerate(self.item_names)}
        target_keys = {name.casefold() for name in target_names}
        if target_keys != set(current):
            raise ValidationError(
                "Correlation matrix item names must match exactly the active risk item names."
            )
        order = [current[name.casefold()] for name in target_names]
        return CorrelationMatrix(target_names, self.values[np.ix_(order, order)])


def _validate_item_names(item_names: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for name in item_names:
        if not isinstance(name, str):
            raise ValidationError("Correlation matrix item names must be strings.")
        normalized = name.strip()
        if not normalized:
            raise ValidationError("Correlation matrix item names must not be empty.")
        key = normalized.casefold()
        if key in seen:
            raise ValidationError("Correlation matrix item names must be unique after trimming.")
        seen.add(key)
        names.append(normalized)
    if not names:
        raise ValidationError("Correlation matrix requires at least one item name.")
    return tuple(names)


def _validate_matrix_values(values: object, dimension: int) -> np.ndarray:
    raw_object = np.asarray(values, dtype=object)
    if any(isinstance(value, bool) for value in raw_object.flat):
        raise ValidationError("Correlation matrix coefficients must be finite real numbers.")
    raw = np.asarray(values)
    if raw.ndim != 2:
        raise ValidationError("Correlation matrix must be two-dimensional.")
    if raw.dtype == np.dtype(bool) or raw.dtype.kind in {"b", "c", "O", "S", "U", "V"}:
        raise ValidationError("Correlation matrix coefficients must be finite real numbers.")
    try:
        array = raw.astype(float, copy=True)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Correlation matrix coefficients must be finite real numbers."
        ) from exc
    if array.shape[0] != array.shape[1]:
        raise ValidationError("Correlation matrix must be square.")
    if array.shape != (dimension, dimension):
        raise ValidationError(
            "Correlation matrix dimension must match the number of active risk items."
        )
    if not np.all(np.isfinite(array)):
        raise ValidationError("Correlation matrix coefficients must be finite real numbers.")
    if not np.all((array >= -1.0) & (array <= 1.0)):
        raise ValidationError("Correlation coefficients must be in [-1, 1].")
    if not np.allclose(np.diag(array), 1.0, atol=DIAGONAL_TOLERANCE, rtol=0.0):
        raise ValidationError("Correlation matrix diagonal coefficients must all be 1.")
    if not np.allclose(array, array.T, atol=SYMMETRY_TOLERANCE, rtol=0.0):
        raise ValidationError("Correlation matrix must be symmetric.")
    try:
        np.linalg.cholesky(array)
    except np.linalg.LinAlgError as exc:
        raise ValidationError("Correlation matrix must be strictly positive definite.") from exc
    array.setflags(write=False)
    return array


def as_correlation_value(value: object, field: str = "correlation coefficient") -> float:
    """Validate one worksheet correlation coefficient."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f"{field} must be a finite real number in [-1, 1].")
    coefficient = float(value)
    if not np.isfinite(coefficient) or not -1 <= coefficient <= 1:
        raise ValidationError(f"{field} must be a finite real number in [-1, 1].")
    return coefficient
