from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from monte_carlo_simulator.analysis import build_tornado_data, compute_spearman_sensitivity
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.visualization.tornado import build_tornado_chart


def test_perfect_monotone_and_deterministic_cases() -> None:
    items = pd.DataFrame({"up": [1, 2, 3, 4], "down": [4, 3, 2, 1], "fixed": [7, 7, 7, 7]})
    result = compute_spearman_sensitivity(items, np.array([1, 2, 3, 4]))
    assert result.loc[result.item_name == "up", "spearman_rho"].item() == pytest.approx(1)
    assert result.loc[result.item_name == "down", "spearman_rho"].item() == pytest.approx(-1)
    fixed = result.loc[result.item_name == "fixed"].iloc[0]
    assert pd.isna(fixed.spearman_rho)
    assert pd.isna(fixed["rank"])
    assert fixed.direction == "undefined"
    assert fixed.is_defined == False  # noqa: E712
    assert fixed.undefined_reason == "constant_input"


def test_nonlinear_negative_event_near_zero_and_single_item() -> None:
    x = np.arange(1, 101, dtype=float)
    nonlinear = x**3
    negative = -x
    event = np.where(x % 4 == 0, 10.0, 0.0)
    noise = np.array([1, -1] * 50, dtype=float)
    items = pd.DataFrame(
        {"nonlinear": nonlinear, "negative": negative, "event": event, "noise": noise}
    )
    result = compute_spearman_sensitivity(items, nonlinear)
    assert result.iloc[0].item_name == "nonlinear"
    assert result.iloc[0].spearman_rho == pytest.approx(1)
    assert result.loc[result.item_name == "negative", "spearman_rho"].item() == pytest.approx(-1)
    assert abs(result.loc[result.item_name == "noise", "spearman_rho"].item()) < 0.02
    assert result.loc[result.item_name == "event", "is_defined"].item() == True  # noqa: E712
    one = compute_spearman_sensitivity(pd.DataFrame({"only": x}), x)
    assert one.loc[0, "spearman_rho"] == pytest.approx(1)
    assert one.loc[0, "rank"] == 1


def test_correlated_inputs_are_supported_without_normalization() -> None:
    rng = np.random.default_rng(123)
    a = rng.normal(size=500)
    b = a * 0.8 + rng.normal(scale=0.2, size=500)
    c = rng.normal(size=500)
    total = a + b + 0.05 * c
    result = compute_spearman_sensitivity(pd.DataFrame({"A": a, "B": b, "C": c}), total)
    assert result.is_defined.all()
    assert np.isfinite(result.spearman_rho).all()
    assert result.item_name.tolist()[:2] == ["A", "B"]
    assert result.absolute_rho.sum() != pytest.approx(1.0)
    assert ((result.spearman_rho >= -1) & (result.spearman_rho <= 1)).all()


def test_deterministic_tie_sort_and_no_input_mutation() -> None:
    items = pd.DataFrame({"A": [1.0, 2.0, 3.0], "B": [1.0, 2.0, 3.0]})
    total = pd.Series([1.0, 2.0, 3.0], index=items.index)
    before = items.copy(deep=True)
    result = compute_spearman_sensitivity(items, total)
    pd.testing.assert_frame_equal(items, before)
    assert result.item_name.tolist() == ["A", "B"]
    assert result["rank"].tolist() == [1, 2]


@pytest.mark.parametrize(
    "items,total",
    [
        ([], np.array([1, 2])),
        (pd.DataFrame(), np.array([1, 2])),
        (pd.DataFrame(index=[0, 1]), np.array([1, 2])),
        (pd.DataFrame({"A": ["1", "2"]}), np.array([1, 2])),
        (pd.DataFrame({"A": [True, False]}), np.array([1, 2])),
        (pd.DataFrame({"A": [1 + 1j, 2 + 0j]}), np.array([1, 2])),
        (pd.DataFrame({"A": [1.0, np.nan]}), np.array([1, 2])),
        (pd.DataFrame({"A": [1.0, np.inf]}), np.array([1, 2])),
        (pd.DataFrame({"A": [1.0, 2.0]}), np.array([[1, 2]])),
        (pd.DataFrame({"A": [1.0, 2.0]}), np.array([1, 2, 3])),
        (pd.DataFrame({"A": [1.0, 2.0]}), np.array([1, 1])),
        (pd.DataFrame({"A": [1.0]}), np.array([1])),
    ],
)
def test_sensitivity_validation_rejects_invalid_inputs(items, total) -> None:
    with pytest.raises(ValidationError):
        compute_spearman_sensitivity(items, total)


def test_sensitivity_rejects_bad_names_and_ambiguous_series_index() -> None:
    with pytest.raises(ValidationError):
        compute_spearman_sensitivity(pd.DataFrame({" ": [1, 2]}), np.array([1, 2]))
    df = pd.DataFrame([[1, 2], [3, 4]], columns=["A", " a "])
    with pytest.raises(ValidationError):
        compute_spearman_sensitivity(df, np.array([3, 7]))
    with pytest.raises(ValidationError):
        compute_spearman_sensitivity(pd.DataFrame({"A": [1, 2]}), pd.Series([1, 2], index=[9, 8]))


@pytest.mark.parametrize("top_n", [0, -1, True, 1.2, "2"])
def test_tornado_top_n_validation(top_n) -> None:
    sensitivity = compute_spearman_sensitivity(pd.DataFrame({"A": [1, 2, 3]}), np.array([1, 2, 3]))
    with pytest.raises(ValidationError):
        build_tornado_data(sensitivity, top_n=top_n)


def test_tornado_data_filters_top_n_and_chart(tmp_path: Path) -> None:
    sensitivity = pd.DataFrame(
        {
            "item_name": ["very long item name " * 3, "negative", "undefined"],
            "spearman_rho": [0.2, -0.8, np.nan],
            "absolute_rho": [0.2, 0.8, np.nan],
            "rank": pd.Series([2, 1, pd.NA], dtype="Int64"),
            "direction": ["positive", "negative", "undefined"],
            "is_defined": [True, True, False],
            "undefined_reason": ["", "", "constant_input"],
        }
    )
    data = build_tornado_data(sensitivity, top_n=1)
    assert data.item_name.tolist() == ["negative"]
    full = build_tornado_data(sensitivity)
    output = tmp_path / "nested" / "tornado.png"
    fig = build_tornado_chart(full, output)
    assert output.exists()
    assert fig.axes[0].get_xlim() == pytest.approx((-1, 1))
    assert fig.axes[0].get_yticklabels()[0].get_text() == "negative"
    plt.close(fig)


def test_tornado_chart_handles_single_positive_and_all_negative() -> None:
    single = pd.DataFrame(
        {"item_name": ["A"], "spearman_rho": [0.01], "absolute_rho": [0.01], "rank": [1]}
    )
    fig = build_tornado_chart(single)
    assert fig.axes[0].get_xlim() == pytest.approx((-1, 1))
    plt.close(fig)
    negatives = pd.DataFrame(
        {
            "item_name": ["B", "C"],
            "spearman_rho": [-0.1, -0.2],
            "absolute_rho": [0.1, 0.2],
            "rank": [2, 1],
        }
    )
    fig = build_tornado_chart(negatives)
    assert fig.axes[0].get_yticklabels()[0].get_text() == "C"
    plt.close(fig)
