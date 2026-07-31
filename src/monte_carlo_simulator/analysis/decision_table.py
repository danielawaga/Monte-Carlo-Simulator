"""Decision-oriented percentile table for project risk simulations."""

from math import isfinite
from numbers import Real

import numpy as np
import pandas as pd

from monte_carlo_simulator.analysis.statistics import format_percentile_label
from monte_carlo_simulator.exceptions import ValidationError

PERCENTILE_TABLE_COLUMNS = (
    "percentile",
    "confidence_level",
    "amount",
    "probability_of_exceedance",
    "baseline",
    "gap_to_baseline",
    "gap_percent",
    "recommended_reserve",
    "unit",
)


def build_percentile_decision_table(
    samples: np.ndarray,
    confidence_levels: tuple[float, ...] = (0.50, 0.80, 0.90),
    *,
    baseline_estimate: float | None = None,
    unit: str | None = None,
) -> pd.DataFrame:
    """Return one decision row per percentile, optionally relative to a baseline."""
    values = _validate_samples(samples)
    levels = _validate_confidence_levels(confidence_levels)
    baseline = _validate_baseline(baseline_estimate)
    normalized_unit = _validate_unit(unit)

    rows: list[dict[str, object]] = []
    for level in levels:
        amount = float(np.quantile(values, level))
        if baseline is None:
            baseline_value = np.nan
            gap = np.nan
            gap_percent = np.nan
            reserve = np.nan
        else:
            baseline_value = baseline
            gap = amount - baseline
            gap_percent = gap / baseline if baseline > 0 else np.nan
            reserve = max(gap, 0.0)
        rows.append(
            {
                "percentile": format_percentile_label(level),
                "confidence_level": level,
                "amount": amount,
                "probability_of_exceedance": 1.0 - level,
                "baseline": baseline_value,
                "gap_to_baseline": gap,
                "gap_percent": gap_percent,
                "recommended_reserve": reserve,
                "unit": normalized_unit or "",
            }
        )
    return pd.DataFrame(rows, columns=list(PERCENTILE_TABLE_COLUMNS))


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


def _validate_confidence_levels(confidence_levels: tuple[float, ...]) -> tuple[float, ...]:
    if not isinstance(confidence_levels, tuple) or not confidence_levels:
        raise ValidationError("confidence_levels must be a non-empty tuple.")
    levels: list[float] = []
    for level in confidence_levels:
        if (
            isinstance(level, bool)
            or not isinstance(level, Real)
            or not isfinite(float(level))
            or not 0 < float(level) < 1
        ):
            raise ValidationError("confidence_levels must contain finite values in (0, 1).")
        levels.append(float(level))
    if len(levels) != len(set(levels)):
        raise ValidationError("confidence_levels must not contain duplicates.")
    return tuple(levels)


def _validate_baseline(baseline_estimate: float | None) -> float | None:
    if baseline_estimate is None:
        return None
    if (
        isinstance(baseline_estimate, bool)
        or not isinstance(baseline_estimate, Real)
        or not isfinite(float(baseline_estimate))
    ):
        raise ValidationError("baseline_estimate must be a finite real value or None.")
    return float(baseline_estimate)


def _validate_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if not isinstance(unit, str) or not unit.strip():
        raise ValidationError("unit must be a non-empty string or None.")
    return unit.strip()
