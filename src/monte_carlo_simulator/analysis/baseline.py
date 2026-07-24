"""Comparison of simulated totals with a project baseline."""

from math import isfinite
from numbers import Real

import numpy as np
import pandas as pd

from monte_carlo_simulator.exceptions import ValidationError


def compute_baseline_comparison(
    samples: np.ndarray,
    baseline_estimate: float,
    confidence_levels: tuple[float, ...] = (0.50, 0.80, 0.90),
) -> pd.DataFrame:
    """Return decision-oriented indicators relative to a reference estimate.

    Relative gaps are undefined for a zero or negative baseline and are returned
    as ``NaN``. A simulated value equal to the baseline is not an exceedance.
    """
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValidationError("samples must be a non-empty one-dimensional finite array.")
    if (
        isinstance(baseline_estimate, bool)
        or not isinstance(baseline_estimate, Real)
        or not isfinite(float(baseline_estimate))
    ):
        raise ValidationError("baseline_estimate must be a finite real value.")
    if not confidence_levels:
        raise ValidationError("confidence_levels must not be empty.")
    levels = tuple(float(level) for level in confidence_levels)
    if any(not isfinite(level) or not 0 < level < 1 for level in levels):
        raise ValidationError("confidence_levels must contain finite values in (0, 1).")
    if len(levels) != len(set(levels)):
        raise ValidationError("confidence_levels must not contain duplicates.")

    baseline = float(baseline_estimate)
    data: dict[str, float] = {
        "baseline": baseline,
        "simulated_mean": float(np.mean(values)),
        "exceedance_probability": float(np.mean(values > baseline)),
    }
    for level in levels:
        label = f"p{format(level * 100, 'g').replace('.', '_')}"
        percentile = float(np.quantile(values, level))
        gap = percentile - baseline
        data[label] = percentile
        data[f"{label}_gap"] = gap
        data[f"{label}_gap_percent"] = gap / baseline if baseline > 0 else np.nan
        data[f"{label}_reserve"] = max(gap, 0.0)

    return pd.DataFrame([data])
