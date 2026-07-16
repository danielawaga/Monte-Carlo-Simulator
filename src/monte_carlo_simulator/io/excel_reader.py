"""Read, validate and convert versioned Excel risk registers."""

from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

import pandas as pd
from openpyxl import load_workbook as openpyxl_load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.workbook.workbook import Workbook

from monte_carlo_simulator.exceptions import (
    RiskRegisterIssue,
    RiskRegisterValidationError,
)
from monte_carlo_simulator.io.schema import (
    METADATA_SHEET,
    OPTIONAL_RISK_REGISTER_COLUMNS,
    REQUIRED_RISK_REGISTER_COLUMNS,
    RISK_REGISTER_COLUMNS,
    RISK_REGISTER_SHEET,
)
from monte_carlo_simulator.io.validators import (
    MetadataCells,
    dataframe_to_validated_risk_items,
    validate_metadata,
)
from monte_carlo_simulator.models import RiskItem, RiskRegister, RiskRegisterMetadata


def load_workbook(file_path: str | Path) -> Workbook:
    """Open an .xlsx workbook and translate expected file errors for end users."""
    path = Path(file_path)
    if not path.exists():
        raise _file_error(path, "The Excel file does not exist.")
    if not path.is_file():
        raise _file_error(path, "The supplied path is not a file.")
    if path.suffix.casefold() != ".xlsx":
        raise _file_error(path, "Schema v1 requires an .xlsx file.")

    try:
        return openpyxl_load_workbook(path, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, KeyError, ParseError, ValueError) as exc:
        raise _file_error(path, f"The file is not a valid readable .xlsx workbook: {exc}") from exc
    except OSError as exc:
        raise _file_error(path, f"The workbook could not be read: {exc}") from exc


def load_metadata(workbook: Workbook) -> RiskRegisterMetadata:
    """Load and validate the metadata sheet of an open workbook."""
    cells, extraction_issues = _extract_metadata_cells(workbook)
    metadata, validation_issues = validate_metadata(cells)
    issues = [*extraction_issues, *validation_issues]
    if issues:
        raise RiskRegisterValidationError(issues)
    if metadata is None:
        raise RuntimeError("Metadata validation succeeded without producing metadata.")
    return metadata


def load_risk_register_dataframe(workbook: Workbook) -> pd.DataFrame:
    """Load risk_register values and retain their original Excel row numbers."""
    dataframe, issues = _extract_risk_register_dataframe(workbook)
    if issues:
        raise RiskRegisterValidationError(issues)
    return dataframe


def dataframe_to_risk_items(
    dataframe: pd.DataFrame,
    metadata: RiskRegisterMetadata,
) -> list[RiskItem]:
    """Validate active DataFrame rows and convert them to RiskItem objects."""
    items, _source_rows, issues = dataframe_to_validated_risk_items(
        dataframe,
        metadata.default_unit,
    )
    if issues:
        raise RiskRegisterValidationError(issues)
    return items


def load_risk_register(file_path: str | Path) -> RiskRegister:
    """Load the complete workbook and return a validated structured risk register."""
    path = Path(file_path)
    workbook = load_workbook(path)
    try:
        metadata_cells, metadata_extraction_issues = _extract_metadata_cells(workbook)
        metadata, metadata_validation_issues = validate_metadata(metadata_cells)
        dataframe, dataframe_issues = _extract_risk_register_dataframe(workbook)
        provisional_unit = (
            metadata.default_unit if metadata else _provisional_default_unit(metadata_cells)
        )
        items, source_rows, row_issues = dataframe_to_validated_risk_items(
            dataframe,
            provisional_unit,
        )
        issues = [
            *metadata_extraction_issues,
            *metadata_validation_issues,
            *dataframe_issues,
            *row_issues,
        ]
        if issues:
            raise RiskRegisterValidationError(issues)
        if metadata is None:
            raise RuntimeError("Workbook validation succeeded without producing metadata.")
        return RiskRegister(
            metadata=metadata,
            items=items,
            source_path=path.resolve(),
            source_rows=source_rows,
        )
    finally:
        workbook.close()


def load_risk_register_excel(file_path: str | Path) -> pd.DataFrame:
    """Compatibility wrapper returning only the validated risk-register DataFrame."""
    workbook = load_workbook(file_path)
    try:
        return load_risk_register_dataframe(workbook)
    finally:
        workbook.close()


def _extract_metadata_cells(
    workbook: Workbook,
) -> tuple[dict[str, tuple[object, int]], list[RiskRegisterIssue]]:
    issues: list[RiskRegisterIssue] = []
    if METADATA_SHEET not in workbook.sheetnames:
        issues.append(
            RiskRegisterIssue(
                sheet=METADATA_SHEET,
                field="sheet",
                value=METADATA_SHEET,
                message=f"Required worksheet '{METADATA_SHEET}' is missing.",
            )
        )
        return {}, issues

    worksheet = workbook[METADATA_SHEET]
    rows = worksheet.iter_rows(values_only=True)
    header = next(rows, None)
    header_values = tuple(header or ())
    if len(header_values) < 2 or _normalized_header(header_values[0]) != "key":
        issues.append(
            RiskRegisterIssue(
                sheet=METADATA_SHEET,
                row=1,
                field="key",
                value=header_values[0] if header_values else None,
                message="Cell A1 must contain the header 'key'.",
            )
        )
    if len(header_values) < 2 or _normalized_header(header_values[1]) != "value":
        issues.append(
            RiskRegisterIssue(
                sheet=METADATA_SHEET,
                row=1,
                field="value",
                value=header_values[1] if len(header_values) > 1 else None,
                message="Cell B1 must contain the header 'value'.",
            )
        )

    cells: dict[str, tuple[object, int]] = {}
    for row_number, row in enumerate(rows, start=2):
        values = tuple(row)
        key_value = values[0] if values else None
        cell_value = values[1] if len(values) > 1 else None
        if _is_blank(key_value) and _is_blank(cell_value):
            continue
        if not isinstance(key_value, str) or not key_value.strip():
            issues.append(
                RiskRegisterIssue(
                    sheet=METADATA_SHEET,
                    row=row_number,
                    field="key",
                    value=key_value,
                    message="Metadata keys must be non-empty text.",
                )
            )
            continue
        key = key_value.strip().casefold()
        if key in cells:
            issues.append(
                RiskRegisterIssue(
                    sheet=METADATA_SHEET,
                    row=row_number,
                    field="key",
                    value=key_value,
                    message=f"Duplicate metadata key; first occurrence is on row {cells[key][1]}.",
                )
            )
            continue
        cells[key] = (cell_value, row_number)
    return cells, issues


def _extract_risk_register_dataframe(
    workbook: Workbook,
) -> tuple[pd.DataFrame, list[RiskRegisterIssue]]:
    issues: list[RiskRegisterIssue] = []
    empty = pd.DataFrame(columns=[*RISK_REGISTER_COLUMNS, "_excel_row"])
    if RISK_REGISTER_SHEET not in workbook.sheetnames:
        issues.append(
            RiskRegisterIssue(
                sheet=RISK_REGISTER_SHEET,
                field="sheet",
                value=RISK_REGISTER_SHEET,
                message=f"Required worksheet '{RISK_REGISTER_SHEET}' is missing.",
            )
        )
        return empty, issues

    worksheet = workbook[RISK_REGISTER_SHEET]
    rows = worksheet.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        issues.append(
            RiskRegisterIssue(
                sheet=RISK_REGISTER_SHEET,
                row=1,
                field="columns",
                value=None,
                message="The risk_register worksheet is empty.",
            )
        )
        return empty, issues

    positions: dict[str, int] = {}
    for position, raw_header in enumerate(header):
        if _is_blank(raw_header):
            continue
        if not isinstance(raw_header, str):
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=1,
                    field="columns",
                    value=raw_header,
                    message="Column headers must be text.",
                )
            )
            continue
        column = raw_header.strip().casefold()
        if column in positions:
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=1,
                    field=column,
                    value=raw_header,
                    message="Duplicate column header.",
                )
            )
            continue
        positions[column] = position

    for column in REQUIRED_RISK_REGISTER_COLUMNS:
        if column not in positions:
            issues.append(
                RiskRegisterIssue(
                    sheet=RISK_REGISTER_SHEET,
                    row=1,
                    field=column,
                    value=None,
                    message=f"Required column '{column}' is missing.",
                )
            )

    records: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=2):
        values = tuple(row)
        record = {
            column: values[position] if position < len(values) else None
            for column, position in positions.items()
            if column in RISK_REGISTER_COLUMNS
        }
        if all(_is_blank(record.get(column)) for column in RISK_REGISTER_COLUMNS):
            continue
        for column in RISK_REGISTER_COLUMNS:
            if column not in record:
                if column == "enabled" and column in OPTIONAL_RISK_REGISTER_COLUMNS:
                    record[column] = True
                else:
                    record[column] = None
        record["_excel_row"] = row_number
        records.append(record)

    return pd.DataFrame(records, columns=[*RISK_REGISTER_COLUMNS, "_excel_row"]), issues


def _provisional_default_unit(cells: MetadataCells) -> str | None:
    value, _row = cells.get("default_unit", (None, 5))
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _normalized_header(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip().casefold()
    return None


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return bool(pd.isna(value))


def _file_error(path: Path, message: str) -> RiskRegisterValidationError:
    return RiskRegisterValidationError(
        [
            RiskRegisterIssue(
                sheet="<workbook>",
                field="file_path",
                value=str(path),
                message=message,
            )
        ]
    )
