"""Spearman rank-correlation sensitivity analysis utilities."""

from __future__ import annotations

import warnings
from numbers import Integral
from typing import Final, cast

import numpy as np
import pandas as pd
from scipy.stats import ConstantInputWarning, spearmanr

from monte_carlo_simulator.exceptions import ValidationError

SENSITIVITY_COLUMNS: Final[tuple[str, ...]] = (
    "item_name",
    "spearman_rho",
    "absolute_rho",
    "rank",
    "direction",
    "is_defined",
    "undefined_reason",
)


def compute_spearman_sensitivity(
    item_samples: pd.DataFrame,
    total_samples: np.ndarray | pd.Series,
) -> pd.DataFrame:
    """Compute per-item Spearman rank correlation against simulated totals."""
    validated_items = _validate_item_samples(item_samples)
    totals = _validate_total_samples(total_samples, validated_items)

    rows: list[dict[str, object]] = []
    for original_index, item_name in enumerate(validated_items.columns):
        values = validated_items[item_name].to_numpy(dtype=float, copy=True)
        if _is_constant(values):
            rows.append(_undefined_row(item_name, "constant_input", original_index))
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConstantInputWarning)
            statistic = spearmanr(values, totals).statistic
        rho = float(statistic)
        if not np.isfinite(rho):
            rows.append(_undefined_row(item_name, "not_calculable", original_index))
            continue
        rho = min(1.0, max(-1.0, rho))
        rows.append(
            {
                "item_name": item_name,
                "spearman_rho": rho,
                "absolute_rho": abs(rho),
                "rank": pd.NA,
                "direction": _direction(rho),
                "is_defined": True,
                "undefined_reason": "",
                "_original_index": original_index,
            }
        )

    result = pd.DataFrame(rows)
    defined = result["is_defined"].astype(bool)
    if defined.any():
        ordered_defined = result.loc[defined].sort_values(
            by=["absolute_rho", "_original_index"], ascending=[False, True], kind="mergesort"
        )
        ranks = pd.Series(range(1, len(ordered_defined) + 1), index=ordered_defined.index)
        result.loc[ordered_defined.index, "rank"] = ranks
    result = result.sort_values(
        by=["is_defined", "absolute_rho", "_original_index"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    result = result.loc[:, list(SENSITIVITY_COLUMNS)].reset_index(drop=True)
    result["rank"] = result["rank"].astype("Int64")
    result["is_defined"] = result["is_defined"].astype(bool)
    return result


def build_tornado_data(sensitivity: pd.DataFrame, top_n: int | None = None) -> pd.DataFrame:
    """Prepare defined Spearman coefficients for tornado-chart rendering."""
    if not isinstance(sensitivity, pd.DataFrame):
        raise ValidationError("sensitivity must be a pandas DataFrame.")
    missing = [column for column in SENSITIVITY_COLUMNS if column not in sensitivity.columns]
    if missing:
        raise ValidationError(f"sensitivity is missing required columns: {', '.join(missing)}.")
    if top_n is not None and (isinstance(top_n, bool) or not isinstance(top_n, Integral)):
        raise ValidationError("top_n must be a strictly positive integer or None.")
    if top_n is not None and top_n <= 0:
        raise ValidationError("top_n must be a strictly positive integer or None.")

    data = sensitivity.loc[sensitivity["is_defined"].astype(bool), list(SENSITIVITY_COLUMNS)].copy()
    data = data.sort_values(
        by=["absolute_rho", "rank", "item_name"],
        ascending=[False, True, True],
        kind="mergesort",
    )
    if top_n is not None:
        data = data.head(int(top_n))
    return data.reset_index(drop=True)


def _validate_item_samples(item_samples: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(item_samples, pd.DataFrame):
        raise ValidationError("item_samples must be a pandas DataFrame.")
    if item_samples.empty:
        raise ValidationError("item_samples must not be empty.")
    if len(item_samples.columns) == 0:
        raise ValidationError("item_samples must contain at least one column.")
    if len(item_samples) < 2:
        raise ValidationError("At least two observations are required.")
    names: list[str] = []
    seen: set[str] = set()
    for column in item_samples.columns:
        if not isinstance(column, str):
            raise ValidationError("item_samples column names must be strings.")
        name = column.strip()
        if not name:
            raise ValidationError("item_samples column names must not be empty.")
        key = name.casefold()
        if key in seen:
            raise ValidationError("item_samples column names must be unique after trimming.")
        seen.add(key)
        names.append(name)
    for name in item_samples.columns:
        series = item_samples[name]
        if pd.api.types.is_bool_dtype(series) or pd.api.types.is_complex_dtype(series):
            raise ValidationError(f"item_samples column '{name}' must contain finite real numbers.")
        if not pd.api.types.is_numeric_dtype(series):
            raise ValidationError(f"item_samples column '{name}' must contain finite real numbers.")
        numeric = series.to_numpy(dtype=float, copy=False)
        if not np.all(np.isfinite(numeric)):
            raise ValidationError(f"item_samples column '{name}' must contain finite real numbers.")
    validated = item_samples.copy(deep=True)
    validated.columns = names
    return validated


def _validate_total_samples(
    total_samples: np.ndarray | pd.Series, item_samples: pd.DataFrame
) -> np.ndarray:
    if isinstance(total_samples, pd.Series):
        if not total_samples.index.equals(item_samples.index):
            raise ValidationError(
                "total_samples Series index must exactly match item_samples index."
            )
        raw = total_samples.to_numpy(copy=False)
    else:
        raw = np.asarray(total_samples)
    if raw.ndim != 1:
        raise ValidationError("total_samples must be one-dimensional.")
    if len(raw) == 0:
        raise ValidationError("total_samples must not be empty.")
    if len(raw) != len(item_samples):
        raise ValidationError("total_samples length must match item_samples rows.")
    if (
        pd.api.types.is_bool_dtype(raw)
        or pd.api.types.is_complex_dtype(raw)
        or raw.dtype.kind in {"O", "S", "U", "V"}
    ):
        raise ValidationError("total_samples must contain finite real numbers.")
    totals = raw.astype(float, copy=True)
    if not np.all(np.isfinite(totals)):
        raise ValidationError("total_samples must contain finite real numbers.")
    if _is_constant(totals):
        raise ValidationError("total_samples must not be constant.")
    return cast(np.ndarray, totals)


def _is_constant(values: np.ndarray) -> bool:
    return bool(np.all(values == values[0]))


def _undefined_row(item_name: str, reason: str, original_index: int) -> dict[str, object]:
    return {
        "item_name": item_name,
        "spearman_rho": np.nan,
        "absolute_rho": np.nan,
        "rank": pd.NA,
        "direction": "undefined",
        "is_defined": False,
        "undefined_reason": reason,
        "_original_index": original_index,
    }


def _direction(rho: float) -> str:
    if rho > 0:
        return "positive"
    if rho < 0:
        return "negative"
    return "neutral"
