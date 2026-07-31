import numpy as np
import pytest

from monte_carlo_simulator.analysis import build_correlation_diagnostics
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import CorrelationMatrix


def test_build_correlation_diagnostics_reports_strict_policy() -> None:
    matrix = CorrelationMatrix(("A", "B"), np.array([[1.0, 0.4], [0.4, 1.0]]))

    diagnostics = build_correlation_diagnostics(matrix)

    assert diagnostics.loc[0, "dimension"] == 2
    assert diagnostics.loc[0, "minimum_eigenvalue"] == pytest.approx(0.6)
    assert diagnostics.loc[0, "maximum_eigenvalue"] == pytest.approx(1.4)
    assert diagnostics.loc[0, "minimum_off_diagonal"] == pytest.approx(0.4)
    assert diagnostics.loc[0, "maximum_off_diagonal"] == pytest.approx(0.4)
    assert bool(diagnostics.loc[0, "strictly_positive_definite"])
    assert diagnostics.loc[0, "policy"] == "strict-no-repair"
    assert not bool(diagnostics.loc[0, "automatic_repair_applied"])


def test_non_positive_definite_matrix_reports_eigenvalue_and_no_repair() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CorrelationMatrix(("A", "B"), np.array([[1.0, 1.0], [1.0, 1.0]]))

    message = str(exc_info.value)
    assert "minimum eigenvalue=" in message
    assert "Automatic repair is disabled" in message
