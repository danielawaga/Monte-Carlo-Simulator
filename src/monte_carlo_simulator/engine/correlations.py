"""Gaussian copula sampling for correlated risk items."""

from collections.abc import Sequence
from numbers import Integral

import numpy as np
from scipy.stats import norm

from monte_carlo_simulator.distributions import BaseDistribution
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import CorrelationMatrix


class GaussianCopulaSampler:
    """Sample marginal distributions through a Gaussian copula."""

    def __init__(self, correlation_matrix: CorrelationMatrix) -> None:
        self.correlation_matrix = correlation_matrix
        self._cholesky = np.linalg.cholesky(correlation_matrix.values)

    def sample(
        self,
        distributions: Sequence[BaseDistribution],
        rng: np.random.Generator,
        number_of_simulations: int,
    ) -> np.ndarray:
        if isinstance(number_of_simulations, bool) or not isinstance(
            number_of_simulations, Integral
        ):
            raise ValidationError("number_of_simulations must be a strictly positive integer.")
        size = int(number_of_simulations)
        if size <= 0:
            raise ValidationError("number_of_simulations must be a strictly positive integer.")
        if not distributions:
            raise ValidationError("At least one distribution is required for correlated sampling.")
        dimension = len(self.correlation_matrix.item_names)
        if len(distributions) != dimension:
            raise ValidationError(
                "Number of distributions must match correlation matrix dimension "
                f"({len(distributions)} != {dimension})."
            )
        if not hasattr(rng, "standard_normal"):
            raise ValidationError("rng must be compatible with numpy.random.Generator.")

        normals = rng.standard_normal(size=(size, dimension))
        correlated = normals @ self._cholesky.T
        probabilities = norm.cdf(correlated)
        return np.column_stack(
            [
                distribution.ppf(probabilities[:, index])
                for index, distribution in enumerate(distributions)
            ]
        )


def apply_correlation_matrix(
    distributions: Sequence[BaseDistribution],
    correlation_matrix: CorrelationMatrix,
    rng: np.random.Generator,
    number_of_simulations: int,
) -> np.ndarray:
    """Sample distributions with the supplied Cholesky-backed Gaussian copula."""
    return GaussianCopulaSampler(correlation_matrix).sample(
        distributions, rng, number_of_simulations
    )
