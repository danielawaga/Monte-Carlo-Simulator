"""Factory converting risk-register rows into probability distributions."""

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.distributions.event import EventDistribution
from monte_carlo_simulator.distributions.lognormal import LogNormalDistribution
from monte_carlo_simulator.distributions.normal import NormalDistribution
from monte_carlo_simulator.distributions.pert import PertDistribution
from monte_carlo_simulator.distributions.triangular import TriangularDistribution
from monte_carlo_simulator.distributions.uniform import UniformDistribution
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem


def build_distribution(item: RiskItem) -> BaseDistribution:
    """Build the probability distribution configured by a risk item."""
    distribution_name = item.distribution

    if distribution_name == "triangular":
        return TriangularDistribution(
            minimum=_required(item.minimum, item, "minimum"),
            most_likely=_required(item.most_likely, item, "most_likely"),
            maximum=_required(item.maximum, item, "maximum"),
        )
    if distribution_name == "pert":
        return PertDistribution(
            minimum=_required(item.minimum, item, "minimum"),
            most_likely=_required(item.most_likely, item, "most_likely"),
            maximum=_required(item.maximum, item, "maximum"),
        )
    if distribution_name == "uniform":
        return UniformDistribution(
            minimum=_required(item.minimum, item, "minimum"),
            maximum=_required(item.maximum, item, "maximum"),
        )
    if distribution_name == "normal":
        return NormalDistribution(
            mean=_required(item.mean, item, "mean"),
            standard_deviation=_required(
                item.standard_deviation, item, "standard_deviation"
            ),
        )
    if distribution_name == "lognormal":
        return LogNormalDistribution(
            mean=_required(item.mean, item, "mean"),
            standard_deviation=_required(
                item.standard_deviation, item, "standard_deviation"
            ),
        )
    if distribution_name == "event":
        return EventDistribution(
            probability=_required(item.probability, item, "probability"),
            impact=_required(item.impact, item, "impact"),
        )

    raise ValidationError(
        f"Unsupported distribution '{item.distribution}' for risk item '{item.name}'."
    )


def _required(value: float | None, item: RiskItem, parameter_name: str) -> float:
    if value is None:
        raise ValidationError(
            f"Risk item '{item.name}' requires parameter '{parameter_name}' "
            f"for distribution '{item.distribution}'."
        )
    return float(value)
