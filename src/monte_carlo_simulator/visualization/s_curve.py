"""Empirical cumulative S-curve visualization."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from monte_carlo_simulator.exceptions import ValidationError


def compute_s_curve_data(samples: np.ndarray) -> pd.DataFrame:
    """Return sorted totals and their empirical cumulative probabilities."""
    values = _validate_samples(samples)
    sorted_values = np.sort(values, kind="mergesort")
    probabilities = np.arange(1, len(sorted_values) + 1, dtype=float) / len(sorted_values)
    return pd.DataFrame({"total": sorted_values, "cumulative_probability": probabilities})


def save_s_curve(
    samples: np.ndarray,
    summary: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "Monte Carlo cumulative S-curve",
    x_label: str = "Total",
) -> Path:
    """Save an empirical cumulative curve with percentile markers."""
    if not isinstance(summary, pd.DataFrame) or summary.empty:
        raise ValidationError("summary must be a non-empty pandas DataFrame.")
    data = compute_s_curve_data(samples)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        ax.step(
            data["total"],
            data["cumulative_probability"],
            where="post",
            linewidth=2,
        )
        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel("Cumulative probability")
        ax.set_ylim(0, 1.01)
        ax.grid(linestyle="--", alpha=0.35)

        percentile_labels = [column for column in summary.columns if column.startswith("P")]
        if percentile_labels:
            colors = plt.colormaps["viridis"](np.linspace(0.2, 0.85, num=len(percentile_labels)))
            for label, color in zip(percentile_labels, colors, strict=True):
                try:
                    level = float(label[1:]) / 100.0
                except ValueError as exc:
                    raise ValidationError(
                        f"Invalid percentile column label in summary: {label!r}."
                    ) from exc
                if not 0 < level < 1:
                    raise ValidationError(f"Invalid percentile column label in summary: {label!r}.")
                value = float(summary.iloc[0][label])
                if not np.isfinite(value):
                    raise ValidationError(f"Percentile value for {label!r} must be finite.")
                ax.axvline(value, color=color, linestyle="--", linewidth=1)
                ax.scatter([value], [level], color=[color], label=f"{label}: {value:.2f}")
            ax.legend()

        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)
    return path


def build_s_curve(
    samples: np.ndarray,
    summary: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "Monte Carlo cumulative S-curve",
    x_label: str = "Total",
) -> Path:
    """Backward-friendly alias for callers using the historical placeholder name."""
    return save_s_curve(
        samples,
        summary,
        output_path,
        title=title,
        x_label=x_label,
    )


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
