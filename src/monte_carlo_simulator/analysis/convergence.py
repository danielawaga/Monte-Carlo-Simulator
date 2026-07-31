"""Convergence diagnostics for cumulative Monte Carlo percentile estimates."""

from math import isfinite
from numbers import Integral, Real

import numpy as np
import pandas as pd

from monte_carlo_simulator.analysis.statistics import format_percentile_label
from monte_carlo_simulator.exceptions import ValidationError

CONVERGENCE_COLUMNS = (
    "draw_count",
    "target_percentile",
    "estimate",
    "absolute_change",
    "relative_change",
    "within_tolerance",
    "consecutive_stable_blocks",
    "stop_recommended",
)


def compute_convergence_diagnostics(
    samples: np.ndarray,
    *,
    confidence_level: float = 0.90,
    block_size: int = 1_000,
    relative_tolerance: float = 0.01,
    required_stable_blocks: int = 3,
    minimum_blocks: int = 4,
) -> pd.DataFrame:
    """Track a cumulative percentile estimate and flag the first stable stopping point.

    The estimate is recomputed on cumulative blocks. A stopping point is recommended when
    the relative change stays within ``relative_tolerance`` for
    ``required_stable_blocks`` consecutive block transitions and at least
    ``minimum_blocks`` cumulative estimates have been observed.
    """
    values = _validate_samples(samples)
    level = _validate_probability(confidence_level, "confidence_level")
    size = _validate_positive_integer(block_size, "block_size")
    stable_blocks = _validate_positive_integer(
        required_stable_blocks, "required_stable_blocks"
    )
    minimum = _validate_positive_integer(minimum_blocks, "minimum_blocks")
    if minimum < 2:
        raise ValidationError("minimum_blocks must be at least 2.")
    if stable_blocks >= minimum:
        raise ValidationError("required_stable_blocks must be smaller than minimum_blocks.")
    if (
        isinstance(relative_tolerance, bool)
        or not isinstance(relative_tolerance, Real)
        or not isfinite(float(relative_tolerance))
        or float(relative_tolerance) <= 0
    ):
        raise ValidationError("relative_tolerance must be a finite strictly positive value.")
    tolerance = float(relative_tolerance)

    endpoints = list(range(size, len(values) + 1, size))
    if not endpoints or endpoints[-1] != len(values):
        endpoints.append(len(values))

    label = format_percentile_label(level)
    rows: list[dict[str, object]] = []
    previous: float | None = None
    consecutive = 0
    stop_selected = False
    for block_index, endpoint in enumerate(endpoints, start=1):
        estimate = float(np.quantile(values[:endpoint], level))
        if previous is None:
            absolute_change = np.nan
            relative_change = np.nan
            within_tolerance = False
        else:
            absolute_change = abs(estimate - previous)
            denominator = max(abs(estimate), abs(previous), np.finfo(float).eps)
            relative_change = absolute_change / denominator
            within_tolerance = bool(relative_change <= tolerance)

        consecutive = consecutive + 1 if within_tolerance else 0
        stop_recommended = bool(
            not stop_selected
            and block_index >= minimum
            and consecutive >= stable_blocks
        )
        if stop_recommended:
            stop_selected = True

        rows.append(
            {
                "draw_count": endpoint,
                "target_percentile": label,
                "estimate": estimate,
                "absolute_change": absolute_change,
                "relative_change": relative_change,
                "within_tolerance": within_tolerance,
                "consecutive_stable_blocks": consecutive,
                "stop_recommended": stop_recommended,
            }
        )
        previous = estimate

    return pd.DataFrame(rows, columns=list(CONVERGENCE_COLUMNS))


def _validate_samples(samples: np.ndarray) -> np.ndarray:
    raw = np.asarray(samples)
    if raw.ndim != 1 or raw.size == 0:
        raise ValidationError("samples must be a non-empty one-dimensional array.")
    if (
        np.issubdtype(raw.dtype, np.bool_)
        or np.issubdtype(raw.dtype, np.complexfloating)
        or raw.dtype.kind in {"O", "S", "U", "V"}
    ):
        raise ValidationError("samples must contain finite real numbers.")
    values = raw.astype(float, copy=True)
    if not np.isfinite(values).all():
        raise ValidationError("samples must contain finite real numbers.")
    return values


def _validate_probability(value: float, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not isfinite(float(value))
        or not 0 < float(value) < 1
    ):
        raise ValidationError(f"{name} must be a finite real value in (0, 1).")
    return float(value)


def _validate_positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValidationError(f"{name} must be a strictly positive integer.")
    return int(value)
