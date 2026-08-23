"""HTTP adapter between the React interface and the Python simulation engine."""

from __future__ import annotations

import tempfile
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from monte_carlo_simulator.access import (
    ACCESS_KEY_HEADER,
    gate_is_enabled,
    log_gate_configuration,
    verify_access_key,
)
from monte_carlo_simulator.application import (
    EditableRiskRegister,
    load_editable_risk_register,
    run_simulation_from_excel,
)
from monte_carlo_simulator.exceptions import RiskRegisterValidationError, ValidationError
from monte_carlo_simulator.io import (
    build_simulation_results_bundle,
    build_simulation_results_workbook,
    create_risk_register_workbook,
)
from monte_carlo_simulator.models import ExcelSimulationRun, SimulationConfig

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPOSITORY_ROOT / "data" / "templates" / "risk_register_template.xlsx"
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
DEFAULT_LEVELS = (0.50, 0.80, 0.90, 0.95)
PUBLIC_PATHS = frozenset({"/api/health"})
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

app = FastAPI(title="Monte Carlo Simulator API", version="0.3.0")
log_gate_configuration()


@app.middleware("http")
async def enforce_access_key(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Reject every request that does not carry the shared secret.

    Preflight requests never carry custom headers, and the health endpoint has
    to stay reachable for deployment probes; everything else is gated.
    """
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    if verify_access_key(request.headers.get(ACCESS_KEY_HEADER)):
        return await call_next(request)
    return JSONResponse(
        status_code=401,
        content={"detail": "Clé d’accès absente ou invalide."},
        headers={"WWW-Authenticate": ACCESS_KEY_HEADER},
    )


# Registered last so it wraps the gate: a 401 still carries the CORS headers the
# browser needs to read it, instead of surfacing as an opaque network error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ProjectMetadataPayload(BaseModel):
    projectName: str
    analysisType: Literal["cost", "duration"] = "cost"
    defaultUnit: str = "EUR"
    baselineEstimate: float | None = None
    description: str = ""


class RiskRowPayload(BaseModel):
    id: str
    name: str
    distribution: Literal["triangular", "pert", "uniform", "normal", "lognormal", "event"]
    minimum: float | None = None
    mostLikely: float | None = None
    maximum: float | None = None
    mean: float | None = None
    standardDeviation: float | None = None
    probability: float | None = None
    impact: float | None = None
    lambdaShape: float | None = None
    category: str = ""
    unit: str = ""
    enabled: bool = True
    notes: str = ""


class CorrelationPayload(BaseModel):
    mode: Literal["independent", "correlated"] = "independent"
    names: list[str] = Field(default_factory=list)
    values: list[list[float]] = Field(default_factory=list)


class RegisterDraftPayload(BaseModel):
    schemaVersion: Literal["1.0"] = "1.0"
    metadata: ProjectMetadataPayload
    items: list[RiskRowPayload]
    correlations: CorrelationPayload = Field(default_factory=CorrelationPayload)


class DraftSimulationConfigPayload(BaseModel):
    simulations: int = 50_000
    seed: int = 42
    levels: list[int] = Field(default_factory=lambda: [50, 80, 90, 95])
    decisionPercentile: int = 80
    exceedanceThreshold: float | None = None
    convergenceTolerance: float = 1.0


class DraftSimulationPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    registerDraft: RegisterDraftPayload = Field(alias="register")
    config: DraftSimulationConfigPayload


class ResultsExportPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    result: dict[str, object]
    registerDraft: RegisterDraftPayload = Field(alias="register")
    config: DraftSimulationConfigPayload


def _parse_levels(raw: str) -> tuple[float, ...]:
    try:
        levels = tuple(float(value.strip()) for value in raw.split(",") if value.strip())
    except ValueError as exc:
        raise ValidationError(
            "Les niveaux de confiance doivent être des nombres séparés par des virgules."
        ) from exc
    return levels or DEFAULT_LEVELS


def _clean(value: object) -> object:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if value is None or pd.isna(value):
        return None
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {str(key): _clean(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _csv(path: Path | None) -> list[dict[str, object]]:
    return [] if path is None or not path.exists() else _records(pd.read_csv(path))


def _payload(run: ExcelSimulationRun, config: SimulationConfig) -> dict[str, object]:
    samples = np.asarray(run.result.samples, dtype=float)
    counts, edges = np.histogram(samples, bins=34)
    ordered = np.sort(samples)
    indexes = np.linspace(0, ordered.size - 1, min(150, ordered.size), dtype=int)
    denominator = max(ordered.size - 1, 1)
    return {
        "project": {
            "name": run.metadata.project_name,
            "analysisType": run.metadata.analysis_type,
            "unit": run.metadata.default_unit,
            "baseline": run.metadata.baseline_estimate,
        },
        "run": {
            "simulations": config.number_of_simulations,
            "seed": config.random_seed,
            "confidenceLevels": list(config.confidence_levels),
            "correlationsEnabled": run.correlation_diagnostics_path is not None,
            "generatedAt": datetime.now(UTC).isoformat(),
        },
        "summary": _records(run.result.summary)[0],
        "percentiles": _csv(run.percentile_table_path),
        "sensitivity": _csv(run.sensitivity_path),
        "convergence": _csv(run.convergence_path),
        "baselineComparison": _csv(run.baseline_comparison_path),
        "correlationDiagnostics": _csv(run.correlation_diagnostics_path),
        "histogram": [
            {"start": float(edges[i]), "end": float(edges[i + 1]), "count": int(count)}
            for i, count in enumerate(counts)
        ],
        "sCurve": [
            {"amount": float(ordered[i]), "probability": float(i / denominator)} for i in indexes
        ],
    }


def _metadata_values(payload: ProjectMetadataPayload) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project_name": payload.projectName,
        "analysis_type": payload.analysisType,
        "default_unit": payload.defaultUnit,
        "baseline_estimate": payload.baselineEstimate,
        "description": payload.description,
    }


def _risk_rows(items: list[RiskRowPayload]) -> list[dict[str, object]]:
    return [
        {
            "name": item.name,
            "distribution": item.distribution,
            "minimum": item.minimum,
            "most_likely": item.mostLikely,
            "maximum": item.maximum,
            "mean": item.mean,
            "standard_deviation": item.standardDeviation,
            "probability": item.probability,
            "impact": item.impact,
            "lambda_shape": item.lambdaShape,
            "category": item.category,
            "unit": item.unit,
            "enabled": item.enabled,
            "notes": item.notes,
        }
        for item in items
    ]


def _write_draft(path: Path, draft: RegisterDraftPayload) -> Path:
    correlation_names = None
    correlation_values = None
    if draft.correlations.mode == "correlated":
        correlation_names = draft.correlations.names
        correlation_values = draft.correlations.values
    return create_risk_register_workbook(
        path,
        metadata_values=_metadata_values(draft.metadata),
        risk_rows=_risk_rows(draft.items),
        correlation_names=correlation_names,
        correlation_values=correlation_values,
    )


def _validate_draft(
    draft: RegisterDraftPayload, directory: Path
) -> tuple[Path, EditableRiskRegister]:
    source = _write_draft(directory / "risk_register.xlsx", draft)
    editable = load_editable_risk_register(source)
    return source, editable


def _draft_from_workbook(path: Path) -> dict[str, object]:
    editable = load_editable_risk_register(path)
    rows = _records(editable.rows)
    items = []
    for index, row in enumerate(rows, start=1):
        items.append(
            {
                "id": f"risk-{index}",
                "name": row.get("name") or "",
                "distribution": row.get("distribution") or "triangular",
                "minimum": row.get("minimum"),
                "mostLikely": row.get("most_likely"),
                "maximum": row.get("maximum"),
                "mean": row.get("mean"),
                "standardDeviation": row.get("standard_deviation"),
                "probability": row.get("probability"),
                "impact": row.get("impact"),
                "lambdaShape": row.get("lambda_shape"),
                "category": row.get("category") or "",
                "unit": row.get("unit") or "",
                "enabled": row.get("enabled") is not False,
                "notes": row.get("notes") or "",
            }
        )
    matrix = editable.correlation_matrix
    correlations = {
        "mode": "correlated" if matrix is not None else "independent",
        "names": list(matrix.item_names) if matrix is not None else [],
        "values": matrix.values.tolist() if matrix is not None else [],
    }
    metadata = editable.metadata
    return {
        "schemaVersion": metadata.schema_version,
        "metadata": {
            "projectName": metadata.project_name,
            "analysisType": metadata.analysis_type,
            "defaultUnit": metadata.default_unit,
            "baselineEstimate": metadata.baseline_estimate,
            "description": metadata.description or "",
        },
        "items": items,
        "correlations": correlations,
    }


async def _read_xlsx(file: UploadFile) -> bytes:
    if Path(file.filename or "").suffix.lower() != ".xlsx":
        raise HTTPException(status_code=415, detail="Seuls les registres .xlsx sont acceptés.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Le classeur dépasse la limite de 12 Mo.")
    return content


@app.get("/api/health")
def health() -> dict[str, str]:
    """Public probe, also used by the interface to discover whether the gate is on."""
    return {
        "status": "ok",
        "engine": "monte-carlo-simulator",
        "accessControl": "enabled" if gate_is_enabled() else "disabled",
    }


@app.get("/api/session")
def session() -> dict[str, bool]:
    """Confirm a submitted key opens the gate, without doing any simulation work."""
    return {"authenticated": True}


@app.get("/api/template")
def template() -> FileResponse:
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Le modèle Excel est indisponible.")
    return FileResponse(TEMPLATE_PATH, filename="risk_register_template.xlsx")


@app.post("/api/simulate")
async def simulate(
    file: Annotated[UploadFile, File()],
    simulations: Annotated[int, Form()] = 10_000,
    seed: Annotated[int, Form()] = 42,
    confidence_levels: Annotated[str, Form()] = "0.50,0.80,0.90,0.95",
) -> dict[str, object]:
    content = await _read_xlsx(file)
    try:
        levels = _parse_levels(confidence_levels)
        config = SimulationConfig(
            number_of_simulations=simulations,
            random_seed=seed,
            confidence_levels=levels,
        )
        with tempfile.TemporaryDirectory(prefix="monte-carlo-web-") as directory:
            root = Path(directory)
            source = root / "risk_register.xlsx"
            output = root / "artifacts"
            output.mkdir()
            source.write_bytes(content)
            run = run_simulation_from_excel(
                source,
                config,
                output_dir=output,
                convergence_confidence_level=max(levels),
            )
            return _payload(run, config)
    except (RiskRegisterValidationError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/register/import")
async def import_register(file: Annotated[UploadFile, File()]) -> dict[str, object]:
    content = await _read_xlsx(file)
    try:
        with tempfile.TemporaryDirectory(prefix="monte-carlo-import-") as directory:
            source = Path(directory) / "risk_register.xlsx"
            source.write_bytes(content)
            return {"register": _draft_from_workbook(source)}
    except (RiskRegisterValidationError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/register/validate")
def validate_register(draft: RegisterDraftPayload) -> dict[str, object]:
    try:
        with tempfile.TemporaryDirectory(prefix="monte-carlo-validate-") as directory:
            _source, editable = _validate_draft(draft, Path(directory))
            active_count = int((editable.rows["enabled"] != False).sum())  # noqa: E712
            return {
                "valid": True,
                "projectName": editable.metadata.project_name,
                "totalItems": len(editable.rows.index),
                "activeItems": active_count,
                "correlationsEnabled": editable.correlation_matrix is not None,
            }
    except (RiskRegisterValidationError, ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/register/export")
def export_register(draft: RegisterDraftPayload) -> Response:
    try:
        with tempfile.TemporaryDirectory(prefix="monte-carlo-export-") as directory:
            source, _editable = _validate_draft(draft, Path(directory))
            content = source.read_bytes()
        return Response(
            content=content,
            media_type=XLSX_MEDIA_TYPE,
            headers={"Content-Disposition": 'attachment; filename="registre_risques.xlsx"'},
        )
    except (RiskRegisterValidationError, ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/register/simulate")
def simulate_register(payload: DraftSimulationPayload) -> dict[str, object]:
    try:
        levels = tuple(level / 100 for level in payload.config.levels)
        config = SimulationConfig(
            number_of_simulations=payload.config.simulations,
            random_seed=payload.config.seed,
            confidence_levels=levels,
        )
        with tempfile.TemporaryDirectory(prefix="monte-carlo-draft-") as directory:
            root = Path(directory)
            source, _editable = _validate_draft(payload.registerDraft, root)
            output = root / "artifacts"
            output.mkdir()
            run = run_simulation_from_excel(
                source,
                config,
                output_dir=output,
                convergence_confidence_level=max(levels),
            )
            return _payload(run, config)
    except (RiskRegisterValidationError, ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/results/export")
def export_results(payload: ResultsExportPayload) -> Response:
    content = build_simulation_results_workbook(
        result=payload.result,
        register=payload.registerDraft.model_dump(by_alias=True),
        config=payload.config.model_dump(),
    )
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="resultats_monte_carlo.xlsx"'},
    )


@app.post("/api/results/export-bundle")
def export_results_bundle(payload: ResultsExportPayload) -> Response:
    with tempfile.TemporaryDirectory(prefix="monte-carlo-bundle-") as directory:
        source, _editable = _validate_draft(payload.registerDraft, Path(directory))
        content = build_simulation_results_bundle(
            result=payload.result,
            register=payload.registerDraft.model_dump(by_alias=True),
            config=payload.config.model_dump(),
            register_workbook=source.read_bytes(),
        )
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="dossier_resultats_monte_carlo.zip"'},
    )
