"""HTTP adapter between the React interface and the Python simulation engine."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

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
from monte_carlo_simulator.storage import accounts
from monte_carlo_simulator.web_auth import (
    Connection,
    CurrentAdmin,
    CurrentUser,
    OptionalUser,
    SessionCookie,
    clear_session_cookie,
    current_user,
    issue_session_cookie,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = REPOSITORY_ROOT / "data" / "templates" / "risk_register_template.xlsx"
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
DEFAULT_LEVELS = (0.50, 0.80, 0.90, 0.95)
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

app = FastAPI(title="Monte Carlo Simulator API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
    # The session cookie only travels on cross-origin calls when credentials
    # are allowed, which is what the Vite dev server needs.
    allow_credentials=True,
)

# Every simulation route requires a signed-in user. Public routes — health,
# first-run setup and sign-in — declare it explicitly by overriding this.
protected = Depends(current_user)


@app.exception_handler(ValidationError)
async def _validation_error(_request: Request, exc: ValidationError) -> JSONResponse:
    """Turn a rejected business rule into 422 rather than a 500.

    Account routes raise ``AccountError`` — a ``ValidationError`` — for a
    duplicate address, a weak password or an attempt to remove the last
    administrator. Without this the caller would see an opaque server error.
    """
    return JSONResponse(status_code=422, content={"detail": str(exc)})


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


class CredentialsPayload(BaseModel):
    email: str
    password: str


class SetupPayload(BaseModel):
    email: str
    fullName: str
    password: str


class NewUserPayload(BaseModel):
    email: str
    fullName: str
    password: str
    role: Literal["admin", "member"] = "member"


class UserUpdatePayload(BaseModel):
    role: Literal["admin", "member"] | None = None
    isActive: bool | None = None


class PasswordChangePayload(BaseModel):
    currentPassword: str
    newPassword: str


def _user_payload(user: accounts.User) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "fullName": user.full_name,
        "role": user.role,
        "isActive": user.is_active,
        "createdAt": user.created_at,
        "lastLoginAt": user.last_login_at,
    }


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
def health(connection: Connection, user: OptionalUser) -> dict[str, object]:
    """Public probe. Also tells the interface which screen to show first."""
    return {
        "status": "ok",
        "engine": "monte-carlo-simulator",
        "setupRequired": not accounts.has_any_user(connection),
        "authenticated": user is not None,
    }


@app.post("/api/setup")
def setup(payload: SetupPayload, response: Response, connection: Connection) -> dict[str, object]:
    """Create the founding administrator on a brand-new installation.

    Deliberately public, and only usable while the database holds no account:
    it is what lets a freshly installed executable be set up from the browser
    without a command line. Create this account right after the first launch.
    """
    admin = accounts.create_first_admin(
        connection,
        email=payload.email,
        full_name=payload.fullName,
        password=payload.password,
    )
    issue_session_cookie(response, accounts.open_session(connection, admin.id))
    return {"user": _user_payload(admin)}


@app.post("/api/auth/login")
def login(
    payload: CredentialsPayload, response: Response, connection: Connection
) -> dict[str, object]:
    user = accounts.authenticate(connection, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Identifiants invalides.")
    issue_session_cookie(response, accounts.open_session(connection, user.id))
    return {"user": _user_payload(user)}


@app.post("/api/auth/logout")
def logout(
    response: Response, connection: Connection, session: SessionCookie = None
) -> dict[str, bool]:
    if session:
        accounts.close_session(connection, session)
    clear_session_cookie(response)
    return {"signedOut": True}


@app.get("/api/auth/me")
def me(user: CurrentUser) -> dict[str, object]:
    return {"user": _user_payload(user)}


@app.post("/api/account/password")
def change_own_password(
    payload: PasswordChangePayload,
    response: Response,
    connection: Connection,
    user: CurrentUser,
) -> dict[str, bool]:
    """Change your own password, after proving you know the current one."""
    if (
        accounts.authenticate(connection, email=user.email, password=payload.currentPassword)
        is None
    ):
        raise HTTPException(status_code=403, detail="Le mot de passe actuel est incorrect.")
    accounts.change_password(connection, user.id, new_password=payload.newPassword)
    # Changing the password closes every session, including this one, so a new
    # cookie is issued to avoid signing the author out of their own browser.
    issue_session_cookie(response, accounts.open_session(connection, user.id))
    return {"changed": True}


@app.get("/api/users")
def list_accounts(connection: Connection, admin: CurrentAdmin) -> dict[str, object]:
    return {"users": [_user_payload(user) for user in accounts.list_users(connection)]}


@app.post("/api/users")
def create_account(
    payload: NewUserPayload, connection: Connection, admin: CurrentAdmin
) -> dict[str, object]:
    created = accounts.create_user(
        connection,
        email=payload.email,
        full_name=payload.fullName,
        password=payload.password,
        role=payload.role,
    )
    return {"user": _user_payload(created)}


@app.patch("/api/users/{user_id}")
def update_account(
    user_id: int, payload: UserUpdatePayload, connection: Connection, admin: CurrentAdmin
) -> dict[str, object]:
    updated = accounts.get_user(connection, user_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Ce compte est introuvable.")
    if payload.role is not None:
        updated = accounts.set_role(connection, user_id, role=payload.role)
    if payload.isActive is not None:
        updated = accounts.set_active(connection, user_id, active=payload.isActive)
    return {"user": _user_payload(updated)}


@app.get("/api/template", dependencies=[protected])
def template() -> FileResponse:
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Le modèle Excel est indisponible.")
    return FileResponse(TEMPLATE_PATH, filename="risk_register_template.xlsx")


@app.post("/api/simulate", dependencies=[protected])
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


@app.post("/api/register/import", dependencies=[protected])
async def import_register(file: Annotated[UploadFile, File()]) -> dict[str, object]:
    content = await _read_xlsx(file)
    try:
        with tempfile.TemporaryDirectory(prefix="monte-carlo-import-") as directory:
            source = Path(directory) / "risk_register.xlsx"
            source.write_bytes(content)
            return {"register": _draft_from_workbook(source)}
    except (RiskRegisterValidationError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/register/validate", dependencies=[protected])
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


@app.post("/api/register/export", dependencies=[protected])
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


@app.post("/api/register/simulate", dependencies=[protected])
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


@app.post("/api/results/export", dependencies=[protected])
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


@app.post("/api/results/export-bundle", dependencies=[protected])
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
