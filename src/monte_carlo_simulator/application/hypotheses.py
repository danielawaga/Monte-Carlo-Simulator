"""Adapters between validated Excel registers and an editable UI model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from monte_carlo_simulator.io import load_risk_register, load_risk_register_excel
from monte_carlo_simulator.models import CorrelationMatrix, RiskRegisterMetadata


@dataclass(frozen=True, slots=True)
class EditableRiskRegister:
    """Validated workbook content in the shape expected by an editable table."""

    metadata: RiskRegisterMetadata
    rows: pd.DataFrame
    correlation_matrix: CorrelationMatrix | None


def load_editable_risk_register(file_path: str | Path) -> EditableRiskRegister:
    """Validate a workbook and expose every row, including disabled ones."""
    register = load_risk_register(file_path)
    rows = load_risk_register_excel(file_path).drop(columns=["_excel_row"], errors="ignore")
    return EditableRiskRegister(
        metadata=register.metadata,
        rows=rows,
        correlation_matrix=register.correlation_matrix,
    )
