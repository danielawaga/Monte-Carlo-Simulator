"""Structured models for a validated Excel risk register and its simulation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from monte_carlo_simulator.models.risk_item import RiskItem
from monte_carlo_simulator.models.simulation_result import SimulationResult

AnalysisType = Literal["cost", "duration"]


@dataclass(frozen=True, slots=True)
class RiskRegisterMetadata:
    """Validated workbook-level information for schema version 1.0."""

    schema_version: str
    project_name: str
    analysis_type: AnalysisType
    default_unit: str
    baseline_estimate: float | None = None
    description: str | None = None


@dataclass(slots=True)
class RiskRegister:
    """Validated risk items together with workbook metadata and source rows."""

    metadata: RiskRegisterMetadata
    items: list[RiskItem]
    source_path: Path | None = None
    source_rows: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class ExcelSimulationRun:
    """Result and artifacts produced by the Excel application workflow."""

    result: SimulationResult
    metadata: RiskRegisterMetadata
    histogram_path: Path
    summary_path: Path
    source_path: Path

    @property
    def artifact_paths(self) -> tuple[Path, Path]:
        """Return all generated artifact paths."""
        return self.histogram_path, self.summary_path
