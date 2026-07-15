"""Monte Carlo simulation engine."""

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from monte_carlo_simulator.analysis.statistics import compute_summary_statistics
from monte_carlo_simulator.distributions import TriangularDistribution
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem, SimulationConfig, SimulationResult

logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """Executes vectorized Monte Carlo simulations."""

    def run(self, items: Sequence[RiskItem], config: SimulationConfig) -> SimulationResult:
        if not items:
            raise ValidationError("At least one risk item is required.")

        rng = np.random.default_rng(config.random_seed)
        item_samples = pd.DataFrame(index=range(config.number_of_simulations))

        for item in items:
            if item.distribution != "triangular":
                raise NotImplementedError(
                    f"Distribution '{item.distribution}' is not implemented in this phase."
                )
            if item.minimum is None or item.most_likely is None or item.maximum is None:
                raise ValidationError(
                    f"Risk item '{item.name}' requires triangular parameters."
                )
            distribution = TriangularDistribution(
                minimum=float(item.minimum),
                most_likely=float(item.most_likely),
                maximum=float(item.maximum),
            )
            item_samples[item.name] = distribution.sample(rng, config.number_of_simulations)

        total_samples = item_samples.sum(axis=1).to_numpy()
        logger.info(
            "Simulation completed for %s items and %s draws.",
            len(items),
            config.number_of_simulations,
        )

        summary = compute_summary_statistics(total_samples, config.confidence_levels)
        return SimulationResult(samples=total_samples, summary=summary, item_samples=item_samples)
