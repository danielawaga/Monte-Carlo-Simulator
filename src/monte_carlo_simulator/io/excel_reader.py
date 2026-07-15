"""Excel input reader."""

from pathlib import Path

import pandas as pd


def load_risk_register_excel(file_path: Path) -> pd.DataFrame:
    """Load risk register data from an Excel file."""
    return pd.read_excel(file_path)
