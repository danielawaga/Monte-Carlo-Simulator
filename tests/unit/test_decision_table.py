import numpy as np
import pytest

from monte_carlo_simulator.analysis.decision_table import build_percentile_decision_table
from monte_carlo_simulator.exceptions import ValidationError


def test_percentile_table_reports_reserve_and_exceedance_probability() -> None:
    table = build_percentile_decision_table(
        np.arange(1, 101, dtype=float),
        baseline_estimate=70,
        unit="EUR",
    )

    assert table["percentile"].tolist() == ["P50", "P80", "P90"]
    assert table["amount"].tolist() == pytest.approx([50.5, 80.2, 90.1])
    assert table["probability_of_exceedance"].tolist() == pytest.approx([0.5, 0.2, 0.1])
    assert table["recommended_reserve"].tolist() == pytest.approx([0.0, 10.2, 20.1])
    assert table["unit"].tolist() == ["EUR", "EUR", "EUR"]


def test_percentile_table_without_baseline_uses_undefined_comparison_fields() -> None:
    table = build_percentile_decision_table(np.array([1.0, 2.0, 3.0]))

    assert table["baseline"].isna().all()
    assert table["gap_to_baseline"].isna().all()
    assert table["recommended_reserve"].isna().all()


def test_percentile_table_rejects_duplicate_levels() -> None:
    with pytest.raises(ValidationError, match="duplicates"):
        build_percentile_decision_table(
            np.array([1.0, 2.0]),
            confidence_levels=(0.8, 0.8),
        )
