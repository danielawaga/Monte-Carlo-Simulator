"""FastAPI adapter used by the S5 React interface.

The web layer deliberately delegates every probabilistic rule to the existing
application service.  It only translates HTTP inputs into ``SimulationConfig``
and serializes the resulting decision artefacts for the browser.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from monte_carlo_simulator.application.service import run_simulation_from_excel
from monte_carlo_simulator.exceptions import RiskRegisterValidationError, ValidationError
from monte_carlo_simulator.models import ExcelSimulationRun, SimulationConfig

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPOSITORY_ROOT / "data" / "templates" / "risk_register_template.xlsx"
FRONTEND_DIST = REPOSITORY_ROOT / "web" / "dist"
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
DEFAULT_LEVELS = (0.50, 0.80, 0.90, 0.95)

app = FastAPI(
    title="Monte Carlo Simulator Web API",
    version="0.2.0",
    description="Thin HTTP adapter over the validated Monte Carlo application service.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _parse_confidence_levels(raw: str) -> tuple[float, ...]:
    try:
        values = tuple(float(part.strip()) for part in raw.split(",") if part.strip())
    except ValueError as exc:
        raise ValidationError("confidence_levels must be comma-separated decimal values.") from exc
    if not values:
        return DEFAULT_LEVELS
    return values


def _clean_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {str(key): _clean_value(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _read_csv_records(path: Path | None) -> list[dict[str, object]]:
    if path is None or not path.exists():
        return []
    return _records(pd.read_csv(path))


def _histogram_payload(samples: np.ndarray, bins: int = 34) -> list[dict[str, float | int]]:
    counts, edges = np.histogram(samples, bins=bins)
    return [
        {
            "start": float(edges[index]),
            "end": float(edges[index + 1]),
            "count": int(counts[index]),
        }
        for index in range(len(counts))
    ]


def _s_curve_payload(samples: np.ndarray, points: int = 150) -> list[dict[str, float]]:
    ordered = np.sort(np.asarray(samples, dtype=float))
    if ordered.size == 0:
        return []
    point_count = min(points, ordered.size)
    indexes = np.linspace(0, ordered.size - 1, point_count, dtype=int)
    denominator = max(ordered.size - 1, 1)
    return [
        {
            "amount": float(ordered[index]),
            "probability": float(index / denominator),
        }
        for index in indexes
    ]


def _simulation_payload(
    run: ExcelSimulationRun, config: SimulationConfig
) -> dict[str, object]:
    result = run.result
    metadata = run.metadata
    summary = _records(result.summary)[0]
    samples = np.asarray(result.samples, dtype=float)

    return {
        "project": {
            "name": metadata.project_name,
            "analysisType": metadata.analysis_type,
            "unit": metadata.default_unit,
            "baseline": metadata.baseline_estimate,
            "description": metadata.description,
        },
        "run": {
            "simulations": config.number_of_simulations,
            "seed": config.random_seed,
            "confidenceLevels": list(config.confidence_levels),
            "correlationsEnabled": run.correlation_diagnostics_path is not None,
            "generatedAt": datetime.now(UTC).isoformat(),
        },
        "summary": summary,
        "percentiles": _read_csv_records(run.percentile_table_path),
        "sensitivity": _read_csv_records(run.sensitivity_path),
        "convergence": _read_csv_records(run.convergence_path),
        "baselineComparison": _read_csv_records(run.baseline_comparison_path),
        "correlationDiagnostics": _read_csv_records(run.correlation_diagnostics_path),
        "histogram": _histogram_payload(samples),
        "sCurve": _s_curve_payload(samples),
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "monte-carlo-simulator"}


@app.get("/api/template")
def download_template() -> FileResponse:
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Risk-register template is unavailable.")
    return FileResponse(
        TEMPLATE_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="risk_register_template.xlsx",
    )


@app.post("/api/simulate")
async def simulate(
    file: Annotated[UploadFile, File()],
    simulations: Annotated[int, Form()] = 10_000,
    seed: Annotated[int, Form()] = 42,
    confidence_levels: Annotated[str, Form()] = "0.50,0.80,0.90,0.95",
) -> JSONResponse:
    filename = file.filename or "risk_register.xlsx"
    if Path(filename).suffix.lower() != ".xlsx":
        raise HTTPException(status_code=415, detail="Only .xlsx risk registers are accepted.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The uploaded workbook exceeds 12 MB.")

    try:
        levels = _parse_confidence_levels(confidence_levels)
        config = SimulationConfig(
            number_of_simulations=simulations,
            random_seed=seed,
            confidence_levels=levels,
        )
        with tempfile.TemporaryDirectory(prefix="monte-carlo-web-") as temporary:
            workdir = Path(temporary)
            source = workdir / "risk_register.xlsx"
            output = workdir / "artifacts"
            output.mkdir(parents=True, exist_ok=True)
            source.write_bytes(content)
            run = run_simulation_from_excel(
                source,
                config,
                output_dir=output,
                convergence_confidence_level=max(levels),
            )
            payload = _simulation_payload(run, config)
    except (RiskRegisterValidationError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return JSONResponse(payload)


if FRONTEND_DIST.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="web-assets")

    @app.get("/{requested_path:path}")
    def serve_frontend(requested_path: str) -> FileResponse:
        del requested_path
        return FileResponse(FRONTEND_DIST / "index.html")
else:

    @app.get("/")
    def development_root() -> dict[str, str]:
        return {
            "message": "Web API is running. Start the Vite client from web/ for the S5 interface.",
            "client": "http://localhost:5173",
        }
