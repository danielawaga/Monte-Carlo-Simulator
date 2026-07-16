"""Histogram generation utilities."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_histogram(
    samples: np.ndarray,
    summary: pd.DataFrame,
    output_path: Path,
    *,
    title: str = "Monte Carlo Total Cost Distribution",
    x_label: str = "Total cost",
) -> Path:
    """Save histogram with percentile markers."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        ax.hist(samples, bins=50, alpha=0.75, edgecolor="black")
        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel("Frequency")

        percentile_labels = [column for column in summary.columns if column.startswith("P")]
        if not summary.empty and percentile_labels:
            colors = plt.colormaps["viridis"](np.linspace(0.2, 0.85, num=len(percentile_labels)))
            for label, color in zip(percentile_labels, colors, strict=True):
                value = float(summary.loc[0, label])
                ax.axvline(value, color=color, linestyle="--", label=f"{label}: {value:.2f}")
            ax.legend()

        fig.tight_layout()
        fig.savefig(output_path)
    finally:
        plt.close(fig)
    return output_path
