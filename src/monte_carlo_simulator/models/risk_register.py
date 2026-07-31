"""Structured models for a validated Excel risk register and its simulation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from monte_carlo_simulator.models.correlation_matrix import CorrelationMatrix
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
    correlation_matrix: CorrelationMatrix | None = None


@dataclass(slots=True)
class ExcelSimulationRun:
    """Result and artifacts produced by the Excel application workflow."""

    result: SimulationResult
    metadata: RiskRegisterMetadata
    histogram_path: Path
    summary_path: Path
    source_path: Path
    sensitivity_path: Path | None = None
    tornado_path: Path | None = None
    baseline_comparison_path: Path | None = None
    s_curve_path: Path | None = None
    percentile_table_path: Path | None = None
    convergence_path: Path | None = None
    correlation_diagnostics_path: Path | None = None

    @property
    def artifact_paths(self) -> tuple[Path, ...]:
        """Return all generated artifact paths."""
        paths = [self.histogram_path, self.summary_path]
        if self.s_curve_path is not None:
            paths.append(self.s_curve_path)
        if self.percentile_table_path is not None:
            paths.append(self.percentile_table_path)
        if self.convergence_path is not None:
            paths.append(self.convergence_path)
        if self.correlation_diagnostics_path is not None:
            paths.append(self.correlation_diagnostics_path)
        if self.sensitivity_path is not None:
            paths.append(self.sensitivity_path)
        if self.tornado_path is not None:
            paths.append(self.tornado_path)
        if self.baseline_comparison_path is not None:
            paths.append(self.baseline_comparison_path)
        return tuple(paths)
