"""Value at Risk utilities."""

import numpy as np


def compute_value_at_risk(samples: np.ndarray, confidence_level: float = 0.95) -> float:
    """Compute VaR as the sample quantile at the chosen confidence level."""
    return float(np.quantile(samples, confidence_level))
