"""Monte Carlo simulation engine."""

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from monte_carlo_simulator.analysis.statistics import compute_summary_statistics
from monte_carlo_simulator.distributions import build_distribution
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem, SimulationConfig, SimulationResult

logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """Execute vectorized Monte Carlo simulations."""

    def run(self, items: Sequence[RiskItem], config: SimulationConfig) -> SimulationResult:
        if not items:
            raise ValidationError("At least one risk item is required.")

        item_names = [item.name for item in items]
        if len(item_names) != len(set(item_names)):
            raise ValidationError("Risk item names must be unique.")

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
