"""Distribution abstraction."""

from abc import ABC, abstractmethod

import numpy as np


class BaseDistribution(ABC):
    """Defines the contract for all probability distributions."""

    @abstractmethod
    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        """Draw vectorized samples from the distribution."""
