"""Pure presentation helpers shared by the interactive application.

The functions in this module deliberately avoid importing Streamlit or Plotly so that
user-facing decision logic stays easy to test and reusable by future interfaces.
"""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

import numpy as np

from monte_carlo_simulator.analysis.statistics import format_percentile_label
from monte_carlo_simulator.exceptions import ValidationError

STANDARD_CONFIDENCE_LEVELS = (0.50, 0.80, 0.90)


@dataclass(frozen=True, slots=True)
class DecisionSnapshot:
    """Small set of indicators highlighted by the interactive interface."""

    confidence_level: float
    percentile_label: str
    percentile_value: float
    mean: float
    baseline_estimate: float | None
    exceedance_probability: float | None
    reserve: float | None


def build_confidence_levels(target_percentage: float) -> tuple[float, ...]:
    """Return standard levels plus the user-selected decision confidence level.

    ``target_percentage`` is expressed as a percentage because this is the natural unit
    exposed in the UI (for example ``90`` for P90). The returned values are probabilities
    accepted by :class:`SimulationConfig`.
    """
    if (
        isinstance(target_percentage, bool)
        or not isinstance(target_percentage, Real)
        or not isfinite(float(target_percentage))
        or not 0 < float(target_percentage) < 100
    ):
        raise ValidationError("target confidence must be a finite percentage in (0, 100).")

    target = float(target_percentage) / 100.0
    levels = {*STANDARD_CONFIDENCE_LEVELS, target}
    return tuple(sorted(levels))


def build_decision_snapshot(
    samples: np.ndarray,
    confidence_level: float,
    baseline_estimate: float | None,
) -> DecisionSnapshot:
    """Compute the indicators needed for a confidence-level decision card."""
    values = np.asarray(samples)
    if values.ndim != 1 or values.size == 0:
        raise ValidationError("samples must be a non-empty one-dimensional array.")
    if (
        np.issubdtype(values.dtype, np.bool_)
        or np.issubdtype(values.dtype, np.complexfloating)
        or values.dtype.kind in {"O", "S", "U", "V"}
    ):
        raise ValidationError("samples must contain finite real numbers.")
    numeric_values = values.astype(float, copy=False)
    if not np.isfinite(numeric_values).all():
        raise ValidationError("samples must contain finite real numbers.")

    if (
        isinstance(confidence_level, bool)
        or not isinstance(confidence_level, Real)
        or not isfinite(float(confidence_level))
        or not 0 < float(confidence_level) < 1
    ):
        raise ValidationError("confidence_level must be a finite value in (0, 1).")
    level = float(confidence_level)

    baseline: float | None
    if baseline_estimate is None:
        baseline = None
    elif (
        isinstance(baseline_estimate, bool)
        or not isinstance(baseline_estimate, Real)
        or not isfinite(float(baseline_estimate))
    ):
        raise ValidationError("baseline_estimate must be a finite real value or None.")
    else:
        baseline = float(baseline_estimate)

    percentile_value = float(np.quantile(numeric_values, level))
    exceedance_probability = None if baseline is None else float(np.mean(numeric_values > baseline))
    reserve = None if baseline is None else max(percentile_value - baseline, 0.0)

    return DecisionSnapshot(
        confidence_level=level,
        percentile_label=format_percentile_label(level),
        percentile_value=percentile_value,
        mean=float(np.mean(numeric_values)),
        baseline_estimate=baseline,
        exceedance_probability=exceedance_probability,
        reserve=reserve,
    )
