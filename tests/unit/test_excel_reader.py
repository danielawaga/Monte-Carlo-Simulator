import math
from pathlib import Path

import pandas as pd
import pytest

from monte_carlo_simulator.exceptions import RiskRegisterValidationError
from monte_carlo_simulator.io import (
    create_risk_register_template,
    dataframe_to_risk_items,
    load_metadata,
    load_risk_register,
    load_risk_register_dataframe,
    load_risk_register_excel,
    load_workbook,
)
from monte_carlo_simulator.models import RiskRegisterMetadata


def _issue_fields(error: RiskRegisterValidationError) -> set[str | None]:
    return {issue.field for issue in error.issues}


def test_generated_template_is_reloaded_with_all_six_distributions(tmp_path: Path) -> None:
    template = create_risk_register_template(tmp_path / "template.xlsx")

    register = load_risk_register(template)

    assert register.metadata.schema_version == "1.0"
    assert register.metadata.analysis_type == "cost"
    assert register.metadata.baseline_estimate == 250_000
    assert [item.distribution for item in register.items] == [
        "triangular",
        "pert",
        "uniform",
        "normal",
        "lognormal",
        "event",
    ]
    assert all(item.unit == "EUR" for item in register.items)
    assert register.items[1].lambda_shape == 4
    assert register.source_rows["Preliminary studies"] == 2


def test_compatibility_dataframe_loader_returns_schema_rows(tmp_path: Path) -> None:
    template = create_risk_register_template(tmp_path / "template.xlsx")

    dataframe = load_risk_register_excel(template)

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 6
    assert dataframe.loc[0, "distribution"] == "triangular"
    assert dataframe.loc[0, "_excel_row"] == 2


def test_explicit_loading_stages_compose_into_risk_items(tmp_path: Path) -> None:
    template = create_risk_register_template(tmp_path / "template.xlsx")
    workbook = load_workbook(template)
    try:
        metadata = load_metadata(workbook)
        dataframe = load_risk_register_dataframe(workbook)
        items = dataframe_to_risk_items(dataframe, metadata)
    finally:
        workbook.close()

    assert metadata.project_name == "Fictitious Infrastructure Project"
    assert len(dataframe) == len(items) == 6
    assert items[-1].distribution == "event"


@pytest.mark.parametrize(
    ("missing_sheet", "factory_arguments"),
    [
        pytest.param("metadata", {"include_metadata": False}, id="metadata"),
        pytest.param(
            "risk_register",
            {"include_risk_register": False},
            id="risk-register",
        ),
    ],
)
def test_required_sheet_absence_is_reported(
    excel_workbook_factory,
    missing_sheet: str,
    factory_arguments: dict[str, object],
) -> None:
    path = excel_workbook_factory(**factory_arguments)

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    assert any(
        issue.sheet == missing_sheet and "missing" in issue.message for issue in caught.value.issues
    )


def test_missing_required_column_is_reported_on_header_row(excel_workbook_factory) -> None:
    path = excel_workbook_factory(omitted_columns=("maximum",))

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issue = next(issue for issue in caught.value.issues if issue.field == "maximum")
    assert issue.sheet == "risk_register"
    assert issue.row == 1
    assert "missing" in issue.message


@pytest.mark.parametrize(
    ("metadata", "field", "message"),
    [
        pytest.param({"analysis_type": "portfolio"}, "analysis_type", "cost", id="analysis"),
        pytest.param({"baseline_estimate": True}, "baseline_estimate", "finite", id="bool"),
        pytest.param({"baseline_estimate": "NaN"}, "baseline_estimate", "finite", id="nan"),
        pytest.param({"baseline_estimate": "inf"}, "baseline_estimate", "finite", id="infinity"),
        pytest.param({"default_unit": "   "}, "default_unit", "required", id="unit"),
        pytest.param({"project_name": 42}, "project_name", "text", id="project-name"),
    ],
)
def test_invalid_metadata_is_contextualized(
    excel_workbook_factory,
    metadata: dict[str, object],
    field: str,
    message: str,
) -> None:
    path = excel_workbook_factory(metadata=metadata)

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issues = [issue for issue in caught.value.issues if issue.field == field]
    assert issues
    assert issues[0].sheet == "metadata"
    assert issues[0].row is not None
    assert message in issues[0].message


def test_unknown_schema_version_is_rejected(excel_workbook_factory) -> None:
    path = excel_workbook_factory(metadata={"schema_version": "2.0"})

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issue = next(issue for issue in caught.value.issues if issue.field == "schema_version")
    assert issue.value == "2.0"
    assert "expected '1.0'" in issue.message


def test_missing_metadata_key_is_reported_once(excel_workbook_factory) -> None:
    path = excel_workbook_factory(omitted_metadata_keys=("project_name",))

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issues = [issue for issue in caught.value.issues if issue.field == "project_name"]
    assert len(issues) == 1
    assert "key" in issues[0].message


def test_disabled_rows_are_completely_ignored(excel_workbook_factory) -> None:
    rows = [
        {
            "name": None,
            "distribution": "not-a-distribution",
            "minimum": True,
            "unit": "USD",
            "enabled": False,
        },
        {
            "name": "Active",
            "distribution": "event",
            "probability": 0,
            "impact": -50,
            "enabled": True,
        },
    ]
    path = excel_workbook_factory(rows=rows)

    register = load_risk_register(path)

    assert [item.name for item in register.items] == ["Active"]
    assert register.items[0].probability == 0
    assert register.items[0].impact == -50


def test_blank_enabled_defaults_to_true_and_default_unit_is_inherited(
    excel_workbook_factory,
) -> None:
    rows = [
        {
            "name": "Inherited unit",
            "distribution": "normal",
            "mean": "125.5",
            "standard_deviation": "0",
            "unit": "  ",
            "enabled": None,
        }
    ]
    path = excel_workbook_factory(rows=rows)

    register = load_risk_register(path)

    assert register.items[0].unit == "EUR"
    assert register.items[0].mean == 125.5
    assert register.items[0].standard_deviation == 0


def test_excel_alias_and_custom_pert_shape_are_converted(excel_workbook_factory) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Custom PERT",
                "distribution": " Beta-PERT ",
                "minimum": "1",
                "most_likely": "2",
                "maximum": "5",
                "lambda_shape": "6.5",
            }
        ]
    )

    register = load_risk_register(path)

    assert register.items[0].distribution == "pert"
    assert register.items[0].lambda_shape == 6.5


def test_enabled_and_notes_columns_may_be_absent(excel_workbook_factory) -> None:
    path = excel_workbook_factory(omitted_columns=("enabled", "notes"))

    register = load_risk_register(path)

    assert len(register.items) == 1
    assert register.items[0].notes is None


def test_incompatible_units_are_rejected(excel_workbook_factory) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Mixed currency",
                "distribution": "uniform",
                "minimum": 1,
                "maximum": 2,
                "unit": "USD",
            }
        ]
    )

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issue = next(issue for issue in caught.value.issues if issue.field == "unit")
    assert issue.row == 2
    assert issue.item_name == "Mixed currency"
    assert issue.value == "USD"
    assert "EUR" in issue.message


def test_units_are_compared_case_insensitively_and_normalized(excel_workbook_factory) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Same currency",
                "distribution": "uniform",
                "minimum": 1,
                "maximum": 2,
                "unit": " eur ",
            }
        ]
    )

    register = load_risk_register(path)

    assert register.items[0].unit == "EUR"


def test_duplicate_names_are_case_insensitive(excel_workbook_factory) -> None:
    rows = [
        {"name": "Permit", "distribution": "uniform", "minimum": 1, "maximum": 2},
        {"name": " permit ", "distribution": "uniform", "minimum": 2, "maximum": 3},
    ]
    path = excel_workbook_factory(rows=rows)

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issue = next(issue for issue in caught.value.issues if "Duplicate item name" in issue.message)
    assert issue.row == 3
    assert issue.item_name == "permit"
    assert "row 2" in issue.message


def test_blank_cells_and_multiple_independent_errors_are_aggregated(
    excel_workbook_factory,
) -> None:
    rows = [
        {
            "name": "   ",
            "distribution": "triangular",
            "minimum": 4,
            "most_likely": None,
            "maximum": 2,
        },
        {
            "name": "Unknown item",
            "distribution": "mystery",
        },
    ]
    path = excel_workbook_factory(rows=rows)

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    assert {"name", "most_likely", "distribution"} <= _issue_fields(caught.value)
    assert len(caught.value.issues) >= 3
    rendered = str(caught.value)
    assert "sheet='risk_register'" in rendered
    assert "row=3" in rendered
    assert "item='Unknown item'" in rendered
    assert "value='mystery'" in rendered


def test_boolean_numeric_parameter_is_rejected_with_cell_context(
    excel_workbook_factory,
) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Boolean minimum",
                "distribution": "uniform",
                "minimum": True,
                "maximum": 2,
            }
        ]
    )

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issue = next(issue for issue in caught.value.issues if issue.field == "minimum")
    assert issue.row == 2
    assert issue.item_name == "Boolean minimum"
    assert issue.value is True
    assert "finite real" in issue.message


@pytest.mark.parametrize("value", ["NaN", "inf", "-inf"])
def test_nan_and_infinite_parameters_are_rejected(
    excel_workbook_factory,
    value: object,
) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Non-finite",
                "distribution": "normal",
                "mean": value,
                "standard_deviation": 1,
            }
        ]
    )

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    assert any(
        issue.field == "mean" and "finite real" in issue.message for issue in caught.value.issues
    )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        pytest.param(math.nan, "required", id="nan-is-blank"),
        pytest.param(math.inf, "finite real", id="positive-infinity"),
        pytest.param(-math.inf, "finite real", id="negative-infinity"),
    ],
)
def test_dataframe_non_finite_values_are_handled(value: float, message: str) -> None:
    dataframe = pd.DataFrame(
        [
            {
                "name": "Non-finite",
                "distribution": "normal",
                "mean": value,
                "standard_deviation": 1,
                "_excel_row": 9,
            }
        ]
    )
    metadata = RiskRegisterMetadata("1.0", "Test", "cost", "EUR")

    with pytest.raises(RiskRegisterValidationError) as caught:
        dataframe_to_risk_items(dataframe, metadata)

    issue = next(issue for issue in caught.value.issues if issue.field == "mean")
    assert issue.row == 9
    assert message in issue.message


def test_dataframe_nan_is_treated_as_a_blank_required_parameter(
    excel_workbook_factory,
) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Blank mean",
                "distribution": "normal",
                "mean": None,
                "standard_deviation": 1,
            }
        ]
    )

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    issue = next(issue for issue in caught.value.issues if issue.field == "mean")
    assert issue.value is None or pd.isna(issue.value)
    assert "required" in issue.message


@pytest.mark.parametrize(
    ("row", "field", "message"),
    [
        pytest.param(
            {
                "name": "Bad order",
                "distribution": "triangular",
                "minimum": 3,
                "most_likely": 2,
                "maximum": 1,
            },
            "most_likely",
            "minimum",
            id="triangular-order",
        ),
        pytest.param(
            {
                "name": "Bad probability",
                "distribution": "event",
                "probability": 1.2,
                "impact": 10,
            },
            "probability",
            "[0, 1]",
            id="probability",
        ),
        pytest.param(
            {
                "name": "Bad deviation",
                "distribution": "normal",
                "mean": 10,
                "standard_deviation": -1,
            },
            "standard_deviation",
            "non-negative",
            id="standard-deviation",
        ),
        pytest.param(
            {
                "name": "Bad lognormal",
                "distribution": "lognormal",
                "mean": 0,
                "standard_deviation": 1,
            },
            "mean",
            "strictly positive",
            id="lognormal-mean",
        ),
        pytest.param(
            {
                "name": "Bad lambda",
                "distribution": "pert",
                "minimum": 1,
                "most_likely": 2,
                "maximum": 3,
                "lambda_shape": 0,
            },
            "lambda_shape",
            "strictly positive",
            id="pert-lambda",
        ),
    ],
)
def test_distribution_domain_errors_are_reported(
    excel_workbook_factory,
    row: dict[str, object],
    field: str,
    message: str,
) -> None:
    path = excel_workbook_factory(rows=[row])

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    assert any(issue.field == field and message in issue.message for issue in caught.value.issues)


@pytest.mark.parametrize("enabled", ["maybe", 2, -1])
def test_invalid_enabled_values_are_rejected(excel_workbook_factory, enabled: object) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Enabled value",
                "distribution": "uniform",
                "minimum": 1,
                "maximum": 2,
                "enabled": enabled,
            }
        ]
    )

    with pytest.raises(RiskRegisterValidationError) as caught:
        load_risk_register(path)

    assert any(issue.field == "enabled" for issue in caught.value.issues)
    assert any("active" in issue.message for issue in caught.value.issues)


def test_nan_enabled_cell_is_treated_as_blank_and_defaults_to_true(
    excel_workbook_factory,
) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Enabled by default",
                "distribution": "uniform",
                "minimum": 1,
                "maximum": 2,
                "enabled": math.nan,
            }
        ]
    )

    register = load_risk_register(path)

    assert [item.name for item in register.items] == ["Enabled by default"]


def test_all_disabled_rows_are_rejected(excel_workbook_factory) -> None:
    path = excel_workbook_factory(
        rows=[
            {
                "name": "Disabled",
                "distribution": "uniform",
                "minimum": 1,
                "maximum": 2,
                "enabled": "FALSE",
            }
        ]
    )

    with pytest.raises(RiskRegisterValidationError, match="active"):
        load_risk_register(path)


def test_nonexistent_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "missing.xlsx"

    with pytest.raises(RiskRegisterValidationError, match="does not exist"):
        load_risk_register(path)


def test_corrupt_xlsx_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.xlsx"
    path.write_bytes(b"not a zip archive")

    with pytest.raises(RiskRegisterValidationError, match="not a valid readable"):
        load_risk_register(path)


def test_non_excel_extension_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "register.csv"
    path.write_text("name,distribution\nA,uniform\n", encoding="utf-8")

    with pytest.raises(RiskRegisterValidationError, match=r"requires an \.xlsx"):
        load_risk_register(path)
