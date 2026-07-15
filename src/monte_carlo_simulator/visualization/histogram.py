"""Histogram generation utilities."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save_histogram(samples: np.ndarray, summary: pd.DataFrame, output_path: Path) -> Path:
    """Save histogram with percentile markers."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(samples, bins=50, alpha=0.75, edgecolor="black")
    ax.set_title("Monte Carlo Total Cost Distribution")
    ax.set_xlabel("Total cost")
    ax.set_ylabel("Frequency")

    if not summary.empty:
        for label, color in (("P50", "tab:green"), ("P80", "tab:orange"), ("P90", "tab:red")):
            if label in summary.columns:
                value = float(summary.loc[0, label])
                ax.axvline(value, color=color, linestyle="--", label=f"{label}: {value:.2f}")
        ax.legend()

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
