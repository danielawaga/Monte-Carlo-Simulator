"""Tests for UI-facing decision presentation helpers."""

import numpy as np
import pytest

from monte_carlo_simulator.application.presentation import (
    build_confidence_levels,
    build_decision_snapshot,
)
from monte_carlo_simulator.exceptions import ValidationError


def test_build_confidence_levels_keeps_standard_levels_and_adds_target() -> None:
    assert build_confidence_levels(95) == (0.50, 0.80, 0.90, 0.95)


def test_build_confidence_levels_does_not_duplicate_standard_target() -> None:
    assert build_confidence_levels(80) == (0.50, 0.80, 0.90)


@pytest.mark.parametrize("value", [True, 0, 100, float("nan"), float("inf")])
def test_build_confidence_levels_rejects_invalid_percentage(value: float) -> None:
    with pytest.raises(ValidationError):
        build_confidence_levels(value)


def test_build_decision_snapshot_with_baseline() -> None:
    snapshot = build_decision_snapshot(
        np.array([10.0, 20.0, 30.0, 40.0]),
        confidence_level=0.75,
        baseline_estimate=25.0,
    )

    assert snapshot.percentile_label == "P75"
    assert snapshot.percentile_value == pytest.approx(32.5)
    assert snapshot.mean == pytest.approx(25.0)
    assert snapshot.exceedance_probability == pytest.approx(0.5)
    assert snapshot.reserve == pytest.approx(7.5)


def test_build_decision_snapshot_without_baseline() -> None:
    snapshot = build_decision_snapshot(
        np.array([1.0, 2.0, 3.0]),
        confidence_level=0.90,
        baseline_estimate=None,
    )

    assert snapshot.percentile_label == "P90"
    assert snapshot.baseline_estimate is None
    assert snapshot.exceedance_probability is None
    assert snapshot.reserve is None


def test_build_decision_snapshot_reserve_never_goes_negative() -> None:
    snapshot = build_decision_snapshot(
        np.array([10.0, 11.0, 12.0]),
        confidence_level=0.90,
        baseline_estimate=20.0,
    )

    assert snapshot.reserve == 0.0
    assert snapshot.exceedance_probability == 0.0


@pytest.mark.parametrize(
    ("samples", "confidence_level"),
    [
        (np.array([]), 0.90),
        (np.array([[1.0, 2.0]]), 0.90),
        (np.array([1.0, np.nan]), 0.90),
        (np.array([1.0, 2.0]), 0.0),
        (np.array([1.0, 2.0]), 1.0),
    ],
)
def test_build_decision_snapshot_rejects_invalid_inputs(
    samples: np.ndarray, confidence_level: float
) -> None:
    with pytest.raises(ValidationError):
        build_decision_snapshot(samples, confidence_level, None)
