"""Simulation output model."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True)
class SimulationResult:
    samples: np.ndarray
    summary: pd.DataFrame
    item_samples: pd.DataFrame | None = None
