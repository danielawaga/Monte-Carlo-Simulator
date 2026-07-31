import numpy as np
import pytest

from monte_carlo_simulator.analysis.convergence import compute_convergence_diagnostics
from monte_carlo_simulator.exceptions import ValidationError


def test_constant_samples_recommend_first_eligible_stable_stop() -> None:
    diagnostics = compute_convergence_diagnostics(
        np.full(50, 10.0),
        block_size=10,
        relative_tolerance=0.001,
        required_stable_blocks=2,
        minimum_blocks=3,
    )

    assert diagnostics["draw_count"].tolist() == [10, 20, 30, 40, 50]
    assert diagnostics["estimate"].tolist() == [10.0] * 5
    assert diagnostics["stop_recommended"].tolist() == [False, False, True, False, False]
    assert diagnostics.loc[2, "consecutive_stable_blocks"] == 2


def test_partial_final_block_is_included() -> None:
    diagnostics = compute_convergence_diagnostics(
        np.arange(23, dtype=float),
        block_size=10,
        required_stable_blocks=1,
        minimum_blocks=2,
    )

    assert diagnostics["draw_count"].tolist() == [10, 20, 23]
    assert diagnostics["target_percentile"].eq("P90").all()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"block_size": 0}, "block_size"),
        ({"confidence_level": 1.0}, "confidence_level"),
        ({"relative_tolerance": 0.0}, "relative_tolerance"),
        ({"required_stable_blocks": 3, "minimum_blocks": 3}, "smaller"),
    ],
)
def test_invalid_convergence_configuration_is_rejected(kwargs, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        compute_convergence_diagnostics(np.arange(20, dtype=float), **kwargs)
