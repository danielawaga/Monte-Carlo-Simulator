"""Monte Carlo simulation engine."""

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from monte_carlo_simulator.analysis.statistics import compute_summary_statistics
from monte_carlo_simulator.distributions import (
    BaseDistribution,
    EventDistribution,
    LogNormalDistribution,
    NormalDistribution,
    PertDistribution,
    TriangularDistribution,
    UniformDistribution,
    build_distribution,
)
from monte_carlo_simulator.engine.correlations import GaussianCopulaSampler
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import (
    CorrelationMatrix,
    RiskItem,
    SimulationConfig,
    SimulationResult,
)

logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """Execute vectorized Monte Carlo simulations."""

    def run(
        self,
        items: Sequence[RiskItem],
        config: SimulationConfig,
        correlation_matrix: CorrelationMatrix | None = None,
    ) -> SimulationResult:
        if not items:
            raise ValidationError("At least one risk item is required.")

        item_names = [item.name.casefold() for item in items]
        if len(item_names) != len(set(item_names)):
            raise ValidationError("Risk item names must be unique (case-insensitive).")

        if correlation_matrix is not None:
            return self._run_correlated(items, config, correlation_matrix)

        rng = np.random.default_rng(config.random_seed)
        item_samples = pd.DataFrame(index=range(config.number_of_simulations))

        for item in items:
            distribution = build_distribution(item)
            item_samples[item.name] = distribution.sample(
                rng=rng,
                size=config.number_of_simulations,
            )

        total_samples = item_samples.sum(axis=1).to_numpy()
        logger.info(
            "Simulation completed for %s items and %s draws.",
            len(items),
            config.number_of_simulations,
        )

        summary = compute_summary_statistics(total_samples, config.confidence_levels)
        return SimulationResult(samples=total_samples, summary=summary, item_samples=item_samples)

    def _run_correlated(
        self,
        items: Sequence[RiskItem],
        config: SimulationConfig,
        correlation_matrix: CorrelationMatrix,
    ) -> SimulationResult:
        names = tuple(item.name for item in items)
        aligned_correlation = correlation_matrix.aligned_to(names)
        distributions = [build_distribution(item) for item in items]
        _validate_deterministic_correlations(distributions, aligned_correlation)

        rng = np.random.default_rng(config.random_seed)
        samples = GaussianCopulaSampler(aligned_correlation).sample(
            distributions,
            rng,
            config.number_of_simulations,
        )
        item_samples = pd.DataFrame(samples, columns=names)
        total_samples = item_samples.sum(axis=1).to_numpy()
        summary = compute_summary_statistics(total_samples, config.confidence_levels)
        return SimulationResult(
            samples=total_samples,
            summary=summary,
            item_samples=item_samples,
            correlation_item_names=names,
            correlation_matrix=aligned_correlation.values.copy(),
        )


def _validate_deterministic_correlations(
    distributions: Sequence[BaseDistribution], correlation_matrix: CorrelationMatrix
) -> None:
    deterministic = [_is_deterministic(distribution) for distribution in distributions]
    for index, is_deterministic in enumerate(deterministic):
        if not is_deterministic:
            continue
        row = correlation_matrix.values[index].copy()
        row[index] = 0.0
        if not np.allclose(row, 0.0, atol=0.0, rtol=0.0):
            item_name = correlation_matrix.item_names[index]
            raise ValidationError(
                "Deterministic risk item "
                f"'{item_name}' cannot have non-zero off-diagonal correlations."
            )


def _is_deterministic(distribution: BaseDistribution) -> bool:
    if isinstance(distribution, (TriangularDistribution, PertDistribution, UniformDistribution)):
        return distribution.minimum == distribution.maximum
    if isinstance(distribution, (NormalDistribution, LogNormalDistribution)):
        return distribution.standard_deviation == 0
    if isinstance(distribution, EventDistribution):
        return distribution.probability in {0, 1} or distribution.impact == 0
    return False
