import numpy as np
import pandas as pd
import pytest

from monte_carlo_simulator.analysis import compute_baseline_comparison
from monte_carlo_simulator.exceptions import ValidationError


def test_baseline_comparison_uses_strict_exceedance_and_computes_indicators() -> None:
    samples = np.array([80, 90, 100, 110, 120], dtype=float)

    result = compute_baseline_comparison(samples, 100)
    row = result.iloc[0]

    assert row["baseline"] == 100
    assert row["simulated_mean"] == 100
    assert row["p50"] == 100
    assert row["p80"] == pytest.approx(112)
    assert row["p90"] == pytest.approx(116)
    assert row["exceedance_probability"] == pytest.approx(0.4)
    assert row["p50_gap"] == 0
    assert row["p80_gap"] == pytest.approx(12)
    assert row["p90_gap"] == pytest.approx(16)
    assert row["p80_gap_percent"] == pytest.approx(0.12)
    assert row["p90_gap_percent"] == pytest.approx(0.16)
    assert row["p80_reserve"] == pytest.approx(12)
    assert row["p90_reserve"] == pytest.approx(16)


def test_reserves_are_never_negative() -> None:
    result = compute_baseline_comparison(np.array([80, 90, 100]), 200)

    assert result.loc[0, "p80_reserve"] == 0
    assert result.loc[0, "p90_reserve"] == 0


@pytest.mark.parametrize("baseline", [0, -100])
def test_relative_gaps_are_undefined_for_non_positive_baseline(baseline: float) -> None:
    result = compute_baseline_comparison(np.array([-20, 0, 20]), baseline)

    assert pd.isna(result.loc[0, "p50_gap_percent"])
    assert pd.isna(result.loc[0, "p80_gap_percent"])
    assert pd.isna(result.loc[0, "p90_gap_percent"])


@pytest.mark.parametrize("baseline", [None, True, np.nan, np.inf])
def test_invalid_baseline_is_rejected(baseline) -> None:
    with pytest.raises(ValidationError, match="baseline_estimate"):
        compute_baseline_comparison(np.array([1, 2, 3]), baseline)


def test_invalid_samples_are_rejected() -> None:
    with pytest.raises(ValidationError, match="samples"):
        compute_baseline_comparison(np.array([]), 100)
