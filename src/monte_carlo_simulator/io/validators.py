"""Validation and conversion helpers for the Excel risk-register schema."""

from collections.abc import Mapping, Sequence
from math import isfinite
from numbers import Real
from typing import cast

import pandas as pd

from monte_carlo_simulator.exceptions import RiskRegisterIssue, ValidationError
from monte_carlo_simulator.io.schema import (
    DISTRIBUTION_REQUIRED_PARAMETERS,
    METADATA_KEYS,
    METADATA_SHEET,
    NUMERIC_RISK_REGISTER_COLUMNS,
    RISK_REGISTER_SHEET,
    SCHEMA_VERSION,
    SUPPORTED_ANALYSIS_TYPES,
)
from monte_carlo_simulator.models import RiskItem, RiskRegisterMetadata
from monte_carlo_simulator.models.risk_item import (
    SUPPORTED_DISTRIBUTIONS,
    normalize_distribution_name,
)
from monte_carlo_simulator.models.risk_register import AnalysisType

MetadataCells = Mapping[str, tuple[object, int]]


def validate_metadata(
    cells: MetadataCells,
) -> tuple[RiskRegisterMetadata | None, list[RiskRegisterIssue]]:
    """Validate raw metadata cells and return the structured v1 metadata."""
    issues: list[RiskRegisterIssue] = []
    for key in METADATA_KEYS:
        if key not in cells:
            issues.append(
                RiskRegisterIssue(
                    sheet=METADATA_SHEET,
                    field=key,
                    value=None,
                    message=f"Required metadata key '{key}' is missing.",
                )
            )

    schema_value, schema_row = cells.get("schema_version", (None, 2))
    schema_version = (
        _required_text(
            schema_value,
            sheet=METADATA_SHEET,
            row=schema_row,
            field="schema_version",
            issues=issues,
        )
        if "schema_version" in cells
        else None
    )
    if schema_version is not None and schema_version != SCHEMA_VERSION:
        issues.append(
            RiskRegisterIssue(
                sheet=METADATA_SHEET,
                row=schema_row,
                field="schema_version",
                value=schema_value,
                message=f"Unsupported schema version; expected '{SCHEMA_VERSION}'.",
            )
        )

    project_value, project_row = cells.get("project_name", (None, 3))
    project_name = (
        _required_text(
            project_value,
            sheet=METADATA_SHEET,
            row=project_row,
            field="project_name",
            issues=issues,
        )
        if "project_name" in cells
        else None
    )

    analysis_value, analysis_row = cells.get("analysis_type", (None, 4))
    analysis_text = (
        _required_text(
            analysis_value,
            sheet=METADATA_SHEET,
            row=analysis_row,
            field="analysis_type",
            issues=issues,
        )
        if "analysis_type" in cells
        else None
    )
    analysis_type = analysis_text.casefold() if analysis_text else None
    if analysis_type is not None and analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        issues.append(
            RiskRegisterIssue(
                sheet=METADATA_SHEET,
                row=analysis_row,
                field="analysis_type",
                value=analysis_value,
                message="analysis_type must be either 'cost' or 'duration'.",
            )
        )

    unit_value, unit_row = cells.get("default_unit", (None, 5))
    default_unit = (
        _required_text(
            unit_value,
            sheet=METADATA_SHEET,
            row=unit_row,
            field="default_unit",
            issues=issues,
        )
        if "default_unit" in cells
        else None
    )

    baseline_value, baseline_row = cells.get("baseline_estimate", (None, 6))
    baseline_estimate = (
        _optional_real(
            baseline_value,
            sheet=METADATA_SHEET,
            row=baseline_row,
            field="baseline_estimate",
            item_name=None,
            issues=issues,
        )
        if "baseline_estimate" in cells
        else None
    )

    description_value, description_row = cells.get("description", (None, 7))
    description = (
        _optional_text(
            description_value,
            sheet=METADATA_SHEET,
            row=description_row,
            field="description",
            item_name=None,
            issues=issues,
        )
        if "description" in cells
        else None
    )

    if issues or schema_version is None or project_name is None:
        return None, issues
    if analysis_type not in SUPPORTED_ANALYSIS_TYPES or default_unit is None:
        return None, issues

    metadata = RiskRegisterMetadata(
        schema_version=schema_version,
        project_name=project_name,
        analysis_type=cast(AnalysisType, analysis_type),
        default_unit=default_unit,
        baseline_estimate=baseline_estimate,
        description=description,
    )
    return metadata, issues


def dataframe_to_validated_risk_items(
    dataframe: pd.DataFrame,
    default_unit: str | None,
) -> tuple[list[RiskItem], dict[str, int], list[RiskRegisterIssue]]:
    """Convert active DataFrame rows to RiskItem objects while collecting row errors."""
    issues: list[RiskRegisterIssue] = []
    items: list[RiskItem] = []
    source_rows: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    active_rows = 0
    expected_unit = default_unit

    for dataframe_index, series in dataframe.iterrows():
        record = series.to_dict()
        excel_row = _excel_row(record.get("_excel_row"), dataframe_index)
        raw_name = record.get("name")
        context_name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None
        enabled = _parse_enabled(record.get("enabled"), excel_row, context_name, issues)
        if enabled is None:
            continue
        if not enabled:
            continue
        active_rows += 1
        row_issue_count = len(issues)

        item_name = _required_text(
            record.get("name"),
            sheet=RISK_REGISTER_SHEET,
            row=excel_row,
            field="name",
            issues=issues,
        )
        distribution_text = _required_text(
            record.get("distribution"),
            sheet=RISK_REGISTER_SHEET,
            row=excel_row,
            field="distribution",
            item_name=item_name,
            issues=issues,
        )
        distribution = normalize_distribution_name(distribution_text) if distribution_text else None
        if distribution is not None and distribution not in SUPPORTED_DISTRIBUTIONS:
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=excel_row,
                    item_name=item_name,
                    field="distribution",
                    value=record.get("distribution"),
                    message=f"Unsupported distribution '{distribution_text}'.",
                )
            )

        if item_name is not None:
            normalized_name = item_name.casefold()
            first_row = seen_names.get(normalized_name)
            if first_row is not None:
                issues.append(
                    RiskRegisterIssue(
                        sheet=RISK_REGISTER_SHEET,
                        row=excel_row,
                        item_name=item_name,
                        field="name",
                        value=record.get("name"),
                        message=f"Duplicate item name; first occurrence is on row {first_row}.",
                    )
                )
            else:
                seen_names[normalized_name] = excel_row

        numeric_values: dict[str, float | None] = {}
        for field in NUMERIC_RISK_REGISTER_COLUMNS:
            numeric_values[field] = _optional_real(
                record.get(field),
                sheet=RISK_REGISTER_SHEET,
                row=excel_row,
                field=field,
                item_name=item_name,
                issues=issues,
            )

        category = _optional_text(
            record.get("category"),
            sheet=RISK_REGISTER_SHEET,
            row=excel_row,
            field="category",
            item_name=item_name,
            issues=issues,
        )
        row_unit = _optional_text(
            record.get("unit"),
            sheet=RISK_REGISTER_SHEET,
            row=excel_row,
            field="unit",
            item_name=item_name,
            issues=issues,
        )
        notes = _optional_text(
            record.get("notes"),
            sheet=RISK_REGISTER_SHEET,
            row=excel_row,
            field="notes",
            item_name=item_name,
            issues=issues,
        )

        resolved_unit = row_unit or default_unit
        if resolved_unit is None:
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=excel_row,
                    item_name=item_name,
                    field="unit",
                    value=record.get("unit"),
                    message="A unit is required when metadata.default_unit is empty.",
                )
            )
        elif expected_unit is None:
            expected_unit = resolved_unit
        elif resolved_unit.casefold() != expected_unit.casefold():
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=excel_row,
                    item_name=item_name,
                    field="unit",
                    value=record.get("unit"),
                    message=f"Unit is incompatible with the register unit '{expected_unit}'.",
                )
            )
        else:
            resolved_unit = expected_unit

        if distribution in DISTRIBUTION_REQUIRED_PARAMETERS:
            for field in DISTRIBUTION_REQUIRED_PARAMETERS[distribution]:
                if numeric_values[field] is None:
                    issues.append(
                        RiskRegisterIssue(
                            sheet=RISK_REGISTER_SHEET,
                            row=excel_row,
                            item_name=item_name,
                            field=field,
                            value=record.get(field),
                            message=f"Parameter is required for distribution '{distribution}'.",
                        )
                    )
            _validate_distribution_domain(
                distribution,
                numeric_values,
                record,
                excel_row,
                item_name,
                issues,
            )

        if len(issues) != row_issue_count:
            continue

        lambda_shape = numeric_values["lambda_shape"]
        try:
            item = RiskItem(
                name=item_name or "",
                distribution=distribution or "",
                minimum=numeric_values["minimum"],
                most_likely=numeric_values["most_likely"],
                maximum=numeric_values["maximum"],
                mean=numeric_values["mean"],
                standard_deviation=numeric_values["standard_deviation"],
                probability=numeric_values["probability"],
                impact=numeric_values["impact"],
                category=category,
                unit=resolved_unit,
                lambda_shape=4.0 if lambda_shape is None else lambda_shape,
                notes=notes,
            )
        except ValidationError as exc:
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=excel_row,
                    item_name=item_name,
                    field="distribution",
                    value=record.get("distribution"),
                    message=str(exc),
                )
            )
            continue
        items.append(item)
        source_rows[item.name] = excel_row

    if active_rows == 0:
        issues.append(
            RiskRegisterIssue(
                sheet=RISK_REGISTER_SHEET,
                field="enabled",
                value=None,
                message="The workbook does not contain any active risk-register row.",
            )
        )

    return items, source_rows, issues


def validate_risk_items(items: Sequence[RiskItem]) -> None:
    """Validate that a collection contains uniquely named RiskItem objects."""
    if not items:
        raise ValidationError("At least one risk item is required.")
    normalized_names = [item.name.casefold() for item in items]
    if len(normalized_names) != len(set(normalized_names)):
        raise ValidationError("Risk item names must be unique (case-insensitive).")


def _validate_distribution_domain(
    distribution: str,
    values: Mapping[str, float | None],
    record: Mapping[object, object],
    row: int,
    item_name: str | None,
    issues: list[RiskRegisterIssue],
) -> None:
    minimum = values["minimum"]
    most_likely = values["most_likely"]
    maximum = values["maximum"]
    standard_deviation = values["standard_deviation"]
    mean = values["mean"]
    probability = values["probability"]
    lambda_shape = values["lambda_shape"]

    if distribution in {"triangular", "pert"}:
        if minimum is not None and most_likely is not None and minimum > most_likely:
            _domain_issue(
                row,
                item_name,
                "most_likely",
                record.get("most_likely"),
                "most_likely must be greater than or equal to minimum.",
                issues,
            )
        if most_likely is not None and maximum is not None and most_likely > maximum:
            _domain_issue(
                row,
                item_name,
                "maximum",
                record.get("maximum"),
                "maximum must be greater than or equal to most_likely.",
                issues,
            )
    elif distribution == "uniform":
        if minimum is not None and maximum is not None and minimum > maximum:
            _domain_issue(
                row,
                item_name,
                "maximum",
                record.get("maximum"),
                "maximum must be greater than or equal to minimum.",
                issues,
            )

    if distribution in {"normal", "lognormal"}:
        if standard_deviation is not None and standard_deviation < 0:
            _domain_issue(
                row,
                item_name,
                "standard_deviation",
                record.get("standard_deviation"),
                "standard_deviation must be non-negative.",
                issues,
            )
        if distribution == "lognormal" and mean is not None and mean <= 0:
            _domain_issue(
                row,
                item_name,
                "mean",
                record.get("mean"),
                "A lognormal mean must be strictly positive.",
                issues,
            )

    if distribution == "event" and probability is not None and not 0 <= probability <= 1:
        _domain_issue(
            row,
            item_name,
            "probability",
            record.get("probability"),
            "probability must be in the interval [0, 1].",
            issues,
        )

    if distribution == "pert" and lambda_shape is not None and lambda_shape <= 0:
        _domain_issue(
            row,
            item_name,
            "lambda_shape",
            record.get("lambda_shape"),
            "lambda_shape must be strictly positive.",
            issues,
        )


def _domain_issue(
    row: int,
    item_name: str | None,
    field: str,
    value: object,
    message: str,
    issues: list[RiskRegisterIssue],
) -> None:
    issues.append(
        RiskRegisterIssue(
            sheet=RISK_REGISTER_SHEET,
            row=row,
            item_name=item_name,
            field=field,
            value=value,
            message=message,
        )
    )


def _parse_enabled(
    value: object,
    row: int,
    item_name: str | None,
    issues: list[RiskRegisterIssue],
) -> bool | None:
    if _is_blank(value):
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, Real) and isfinite(float(value)) and float(value) in {0.0, 1.0}:
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
    issues.append(
        RiskRegisterIssue(
            sheet=RISK_REGISTER_SHEET,
            row=row,
            item_name=item_name,
            field="enabled",
            value=value,
            message="enabled must be TRUE, FALSE, 1, 0 or empty.",
        )
    )
    return None


def _required_text(
    value: object,
    *,
    sheet: str,
    row: int | None,
    field: str,
    issues: list[RiskRegisterIssue],
    item_name: str | None = None,
) -> str | None:
    if _is_blank(value):
        issues.append(
            RiskRegisterIssue(
                sheet=sheet,
                row=row,
                item_name=item_name,
                field=field,
                value=value,
                message=f"{field} is required and must not be blank.",
            )
        )
        return None
    if not isinstance(value, str):
        issues.append(
            RiskRegisterIssue(
                sheet=sheet,
                row=row,
                item_name=item_name,
                field=field,
                value=value,
                message=f"{field} must be text.",
            )
        )
        return None
    return value.strip()


def _optional_text(
    value: object,
    *,
    sheet: str,
    row: int | None,
    field: str,
    item_name: str | None,
    issues: list[RiskRegisterIssue],
) -> str | None:
    if _is_blank(value):
        return None
    if not isinstance(value, str):
        issues.append(
            RiskRegisterIssue(
                sheet=sheet,
                row=row,
                item_name=item_name,
                field=field,
                value=value,
                message=f"{field} must be text when provided.",
            )
        )
        return None
    return value.strip()


def _optional_real(
    value: object,
    *,
    sheet: str,
    row: int | None,
    field: str,
    item_name: str | None,
    issues: list[RiskRegisterIssue],
) -> float | None:
    if _is_blank(value):
        return None
    if isinstance(value, bool):
        _numeric_issue(value, sheet, row, field, item_name, issues)
        return None

    numeric_value: float
    if isinstance(value, Real):
        numeric_value = float(value)
    elif isinstance(value, str):
        try:
            numeric_value = float(value.strip())
        except ValueError:
            _numeric_issue(value, sheet, row, field, item_name, issues)
            return None
    else:
        _numeric_issue(value, sheet, row, field, item_name, issues)
        return None

    if not isfinite(numeric_value):
        _numeric_issue(value, sheet, row, field, item_name, issues)
        return None
    return numeric_value


def _numeric_issue(
    value: object,
    sheet: str,
    row: int | None,
    field: str,
    item_name: str | None,
    issues: list[RiskRegisterIssue],
) -> None:
    issues.append(
        RiskRegisterIssue(
            sheet=sheet,
            row=row,
            item_name=item_name,
            field=field,
            value=value,
            message=f"{field} must be a finite real number; numeric text is accepted.",
        )
    )


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def _excel_row(value: object, dataframe_index: object) -> int:
    if isinstance(value, Real) and not isinstance(value, bool):
        return int(float(value))
    if isinstance(dataframe_index, int):
        return dataframe_index + 2
    return 2
