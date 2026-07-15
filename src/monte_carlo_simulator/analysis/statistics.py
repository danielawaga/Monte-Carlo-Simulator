"""Statistical analysis helpers."""

import numpy as np
import pandas as pd


def compute_summary_statistics(
    samples: np.ndarray, confidence_levels: tuple[float, ...] = (0.50, 0.80, 0.90)
) -> pd.DataFrame:
    """Return summary statistics for a sample vector."""
    summary: dict[str, float] = {
        "mean": float(np.mean(samples)),
        "median": float(np.median(samples)),
        "std": float(np.std(samples, ddof=0)),
        "minimum": float(np.min(samples)),
        "maximum": float(np.max(samples)),
    }
    for level in confidence_levels:
        label = f"P{int(level * 100)}"
        summary[label] = float(np.quantile(samples, level))
    return pd.DataFrame([summary])
