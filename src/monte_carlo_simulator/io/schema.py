"""Versioned constants for the Excel risk-register schema."""

SCHEMA_VERSION = "1.0"
METADATA_SHEET = "metadata"
RISK_REGISTER_SHEET = "risk_register"
INSTRUCTIONS_SHEET = "instructions"

METADATA_KEYS = (
    "schema_version",
    "project_name",
    "analysis_type",
    "default_unit",
    "baseline_estimate",
    "description",
)

RISK_REGISTER_COLUMNS = (
    "name",
    "distribution",
    "minimum",
    "most_likely",
    "maximum",
    "mean",
    "standard_deviation",
    "probability",
    "impact",
    "lambda_shape",
    "category",
    "unit",
    "enabled",
    "notes",
)

OPTIONAL_RISK_REGISTER_COLUMNS = frozenset({"enabled", "notes"})
REQUIRED_RISK_REGISTER_COLUMNS = tuple(
    column for column in RISK_REGISTER_COLUMNS if column not in OPTIONAL_RISK_REGISTER_COLUMNS
)
NUMERIC_RISK_REGISTER_COLUMNS = (
    "minimum",
    "most_likely",
    "maximum",
    "mean",
    "standard_deviation",
    "probability",
    "impact",
    "lambda_shape",
)

DISTRIBUTION_REQUIRED_PARAMETERS: dict[str, tuple[str, ...]] = {
    "triangular": ("minimum", "most_likely", "maximum"),
    "pert": ("minimum", "most_likely", "maximum"),
    "uniform": ("minimum", "maximum"),
    "normal": ("mean", "standard_deviation"),
    "lognormal": ("mean", "standard_deviation"),
    "event": ("probability", "impact"),
}

SUPPORTED_ANALYSIS_TYPES = frozenset({"cost", "duration"})
