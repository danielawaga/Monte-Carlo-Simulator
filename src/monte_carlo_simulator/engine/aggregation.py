"""Aggregation helpers."""

import pandas as pd


def aggregate_total(item_samples: pd.DataFrame) -> pd.Series:
    """Aggregate line-item samples into one total sample vector."""
    return item_samples.sum(axis=1)
