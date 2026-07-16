import numpy as np
import pytest

from monte_carlo_simulator.analysis.statistics import (
    compute_summary_statistics,
    format_percentile_label,
)
from monte_carlo_simulator.exceptions import ValidationError


def test_percentiles_are_ordered() -> None:
    rng = np.random.default_rng(42)
    samples = rng.normal(loc=100.0, scale=20.0, size=10_000)

    summary = compute_summary_statistics(samples)

    p50 = float(summary.loc[0, "P50"])
    p80 = float(summary.loc[0, "P80"])
    p90 = float(summary.loc[0, "P90"])

    assert p50 <= p80 <= p90


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        pytest.param(0.50, "P50", id="integer-percentage"),
        pytest.param(0.95, "P95", id="ninety-five"),
        pytest.param(0.951, "P95.1", id="one-decimal"),
        pytest.param(0.995, "P99.5", id="ninety-nine-point-five"),
    ],
)
def test_percentile_labels_preserve_significant_decimals(level: float, expected: str) -> None:
    assert format_percentile_label(level) == expected


def test_decimal_percentile_levels_do_not_collide() -> None:
    samples = np.arange(100, dtype=float)

    summary = compute_summary_statistics(samples, (0.951, 0.959, 0.995))

    assert {"P95.1", "P95.9", "P99.5"} <= set(summary.columns)
    assert summary.columns.is_unique


def test_remaining_duplicate_percentile_label_is_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        compute_summary_statistics(np.arange(10, dtype=float), (0.95, 0.950))
