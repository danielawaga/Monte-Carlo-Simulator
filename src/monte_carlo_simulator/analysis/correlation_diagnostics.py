"""Decision-safe diagnostics for validated correlation matrices.

This module is intentionally descriptive only: it never projects, jitters, clips or
otherwise repairs a user-supplied matrix.
"""

import numpy as np
import pandas as pd

from monte_carlo_simulator.models.correlation_matrix import CorrelationMatrix

CORRELATION_DIAGNOSTIC_COLUMNS = (
    "dimension",
    "minimum_eigenvalue",
    "maximum_eigenvalue",
    "condition_number",
    "determinant",
    "minimum_off_diagonal",
    "maximum_off_diagonal",
    "strictly_positive_definite",
    "policy",
    "automatic_repair_applied",
)


def build_correlation_diagnostics(matrix: CorrelationMatrix) -> pd.DataFrame:
    """Summarize numerical health without modifying the validated matrix."""
    values = matrix.values
    eigenvalues = np.linalg.eigvalsh(values)
    off_diagonal = values[~np.eye(values.shape[0], dtype=bool)]

    minimum_off_diagonal = float(np.min(off_diagonal)) if off_diagonal.size else np.nan
    maximum_off_diagonal = float(np.max(off_diagonal)) if off_diagonal.size else np.nan

    row = {
        "dimension": values.shape[0],
        "minimum_eigenvalue": float(np.min(eigenvalues)),
        "maximum_eigenvalue": float(np.max(eigenvalues)),
        "condition_number": float(np.linalg.cond(values)),
        "determinant": float(np.linalg.det(values)),
        "minimum_off_diagonal": minimum_off_diagonal,
        "maximum_off_diagonal": maximum_off_diagonal,
        "strictly_positive_definite": bool(np.min(eigenvalues) > 0.0),
        "policy": "strict-no-repair",
        "automatic_repair_applied": False,
    }
    return pd.DataFrame([row], columns=list(CORRELATION_DIAGNOSTIC_COLUMNS))
