from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.visualization.s_curve import compute_s_curve_data, save_s_curve


def test_s_curve_data_is_sorted_and_reaches_one() -> None:
    data = compute_s_curve_data(np.array([3.0, 1.0, 2.0]))

    assert data["total"].tolist() == [1.0, 2.0, 3.0]
    assert data["cumulative_probability"].tolist() == pytest.approx([1 / 3, 2 / 3, 1.0])


def test_s_curve_is_saved_with_decimal_percentile_labels(tmp_path: Path) -> None:
    path = save_s_curve(
        np.arange(1, 101, dtype=float),
        pd.DataFrame([{"P50": 50.5, "P95.1": 95.149}]),
        tmp_path / "s_curve.png",
    )

    assert path.exists()
    assert path.stat().st_size > 0


def test_s_curve_rejects_invalid_percentile_label(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="Invalid percentile column label"):
        save_s_curve(
            np.array([1.0, 2.0]),
            pd.DataFrame([{"Percentile": 1.5, "Pbad": 1.5}]),
            tmp_path / "bad.png",
        )
