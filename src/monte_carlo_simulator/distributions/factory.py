"""Factory converting risk-register rows into probability distributions."""

from collections.abc import Callable

from monte_carlo_simulator.distributions.base import BaseDistribution
from monte_carlo_simulator.distributions.event import EventDistribution
from monte_carlo_simulator.distributions.lognormal import LogNormalDistribution
from monte_carlo_simulator.distributions.normal import NormalDistribution
from monte_carlo_simulator.distributions.pert import PertDistribution
from monte_carlo_simulator.distributions.triangular import TriangularDistribution
from monte_carlo_simulator.distributions.uniform import UniformDistribution
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem


def _build_triangular(item: RiskItem) -> BaseDistribution:
    return TriangularDistribution(
        minimum=_required(item.minimum, item, "minimum"),
        most_likely=_required(item.most_likely, item, "most_likely"),
        maximum=_required(item.maximum, item, "maximum"),
    )


def _build_pert(item: RiskItem) -> BaseDistribution:
    return PertDistribution(
        minimum=_required(item.minimum, item, "minimum"),
        most_likely=_required(item.most_likely, item, "most_likely"),
        maximum=_required(item.maximum, item, "maximum"),
        lambda_shape=_required(item.lambda_shape, item, "lambda_shape"),
    )


def _build_uniform(item: RiskItem) -> BaseDistribution:
    return UniformDistribution(
        minimum=_required(item.minimum, item, "minimum"),
        maximum=_required(item.maximum, item, "maximum"),
    )


def _build_normal(item: RiskItem) -> BaseDistribution:
    return NormalDistribution(
        mean=_required(item.mean, item, "mean"),
        standard_deviation=_required(item.standard_deviation, item, "standard_deviation"),
    )


def _build_lognormal(item: RiskItem) -> BaseDistribution:
    return LogNormalDistribution(
        mean=_required(item.mean, item, "mean"),
        standard_deviation=_required(item.standard_deviation, item, "standard_deviation"),
    )


def _build_event(item: RiskItem) -> BaseDistribution:
    return EventDistribution(
        probability=_required(item.probability, item, "probability"),
        impact=_required(item.impact, item, "impact"),
    )


_DISTRIBUTION_BUILDERS: dict[str, Callable[[RiskItem], BaseDistribution]] = {
    "triangular": _build_triangular,
    "pert": _build_pert,
    "uniform": _build_uniform,
    "normal": _build_normal,
    "lognormal": _build_lognormal,
    "event": _build_event,
}


def build_distribution(item: RiskItem) -> BaseDistribution:
    """Build the probability distribution configured by a risk item."""
    builder = _DISTRIBUTION_BUILDERS.get(item.distribution)
    if builder is None:
        raise ValidationError(
            f"Unsupported distribution '{item.distribution}' for risk item '{item.name}'."
        )
    return builder(item)


def _required(value: float | None, item: RiskItem, parameter_name: str) -> float:
    if value is None:
        raise ValidationError(
            f"Risk item '{item.name}' requires parameter '{parameter_name}' "
            f"for distribution '{item.distribution}'."
        )
    return value
