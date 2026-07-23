"""Matplotlib tornado chart for Spearman sensitivity coefficients."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from monte_carlo_simulator.exceptions import ValidationError


def build_tornado_chart(
    tornado_data: pd.DataFrame,
    output_path: str | Path | None = None,
    *,
    title: str = "Analyse de sensibilité — corrélation de rang de Spearman",
) -> Figure:
    """Render a horizontal tornado chart centered on zero."""
    if not isinstance(tornado_data, pd.DataFrame):
        raise ValidationError("tornado_data must be a pandas DataFrame.")
    required = {"item_name", "spearman_rho", "absolute_rho"}
    missing = required.difference(tornado_data.columns)
    if missing:
        raise ValidationError(
            f"tornado_data is missing required columns: {', '.join(sorted(missing))}."
        )

    data = tornado_data.sort_values(
        by=["absolute_rho", "rank", "item_name"], ascending=[False, True, True], kind="mergesort"
    ).reset_index(drop=True)
    height = max(3.0, 1.0 + 0.55 * max(len(data), 1))
    fig, ax = plt.subplots(figsize=(11, height))
    try:
        y_positions = list(range(len(data)))
        values = data["spearman_rho"].astype(float).tolist()
        colors = ["#4C78A8" if value >= 0 else "#F58518" for value in values]
        ax.barh(y_positions, values, color=colors, alpha=0.85)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(data["item_name"].astype(str).tolist())
        ax.invert_yaxis()
        ax.axvline(0, color="black", linewidth=1)
        ax.set_xlim(-1, 1)
        ax.set_xlabel("Coefficient de Spearman (ρ)")
        ax.set_title(title)
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        for y_position, value in zip(y_positions, values, strict=True):
            offset = 0.025 if value >= 0 else -0.025
            ha = "left" if value >= 0 else "right"
            ax.text(value + offset, y_position, f"{value:+.3f}", va="center", ha=ha, fontsize=9)
        fig.tight_layout()
        if output_path is not None:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, bbox_inches="tight")
        return fig
    finally:
        if output_path is not None:
            plt.close(fig)
