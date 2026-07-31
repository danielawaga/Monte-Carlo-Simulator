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


def export_baseline_comparison_to_csv(comparison: pd.DataFrame, output_path: Path) -> None:
    """Export baseline comparison indicators to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output_path, index=False)


def export_percentile_table_to_csv(table: pd.DataFrame, output_path: Path) -> None:
    """Export the decision-oriented percentile table to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_path, index=False)


def export_convergence_to_csv(diagnostics: pd.DataFrame, output_path: Path) -> None:
    """Export cumulative percentile convergence diagnostics to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics.to_csv(output_path, index=False)


def export_correlation_diagnostics_to_csv(diagnostics: pd.DataFrame, output_path: Path) -> None:
    """Export strict correlation-matrix health diagnostics to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics.to_csv(output_path, index=False)
