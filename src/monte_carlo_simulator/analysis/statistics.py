"""Statistical analysis helpers."""

from decimal import Decimal
from math import isfinite
from numbers import Real

import numpy as np
import pandas as pd

from monte_carlo_simulator.exceptions import ValidationError


def format_percentile_label(level: float) -> str:
    """Format a quantile level without truncating its significant decimals."""
    if (
        isinstance(level, bool)
        or not isinstance(level, Real)
        or not isfinite(float(level))
        or not 0 < float(level) < 1
    ):
        raise ValidationError("Percentile levels must be finite real values in (0, 1).")

    percentage = Decimal(str(float(level))) * Decimal(100)
    text = format(percentage, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"P{text}"


def compute_summary_statistics(
    samples: np.ndarray, confidence_levels: tuple[float, ...] = (0.50, 0.80, 0.90)
) -> pd.DataFrame:
    """Return summary statistics for a sample vector."""
    labels = [format_percentile_label(level) for level in confidence_levels]
    if len(labels) != len(set(labels)):
        raise ValidationError("confidence_levels produce duplicate percentile labels.")

    summary: dict[str, float] = {
        "mean": float(np.mean(samples)),
        "median": float(np.median(samples)),
        "std": float(np.std(samples, ddof=0)),
        "minimum": float(np.min(samples)),
        "maximum": float(np.max(samples)),
    }
    for level, label in zip(confidence_levels, labels, strict=True):
        summary[label] = float(np.quantile(samples, level))
    return pd.DataFrame([summary])
