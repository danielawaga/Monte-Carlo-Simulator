"""Export helpers for simulation outputs."""

from pathlib import Path

import pandas as pd


def export_summary_to_csv(summary: pd.DataFrame, output_path: Path) -> None:
    """Export summary statistics to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)


def export_sensitivity_to_csv(sensitivity: pd.DataFrame, output_path: Path) -> None:
    """Export Spearman sensitivity analysis to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sensitivity.to_csv(output_path, index=False)
