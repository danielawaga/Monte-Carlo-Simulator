import math
from collections.abc import Callable

import pytest

from monte_carlo_simulator.distributions import (
    EventDistribution,
    LogNormalDistribution,
    NormalDistribution,
    PertDistribution,
    TriangularDistribution,
    UniformDistribution,
    build_distribution,
)
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.models import RiskItem


def _make_item(distribution: str, **overrides: object) -> RiskItem:
    canonical_name = distribution.strip().casefold().replace("_", "-")
    if "pert" in canonical_name:
        parameters: dict[str, object] = {
            "minimum": 1,
            "most_likely": 2,
            "maximum": 4,
        }
    elif canonical_name == "triangular":
        parameters = {"minimum": 1, "most_likely": 2, "maximum": 4}
    elif canonical_name == "uniform":
        parameters = {"minimum": 1, "maximum": 4}
    elif canonical_name in {"normal", "lognormal", "log-normal", "log normal"}:
        parameters = {"mean": 2, "standard_deviation": 0.5}
    else:
        parameters = {"probability": 0.25, "impact": -4}
    parameters.update(overrides)
    return RiskItem("Example", distribution, **parameters)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("distribution_name", "canonical_name"),
    [
        pytest.param(" triangular ", "triangular", id="triangular"),
        pytest.param("PERT", "pert", id="pert"),
        pytest.param("Beta-PERT", "pert", id="beta-pert"),
        pytest.param("beta_pert", "pert", id="beta-pert-underscore"),
        pytest.param("beta pert", "pert", id="beta-pert-space"),
        pytest.param("uniform", "uniform", id="uniform"),
        pytest.param("normal", "normal", id="normal"),
        pytest.param("lognormal", "lognormal", id="lognormal"),
        pytest.param("log-normal", "lognormal", id="lognormal-hyphen"),
        pytest.param("log_normal", "lognormal", id="lognormal-underscore"),
        pytest.param("log normal", "lognormal", id="lognormal-space"),
        pytest.param("event", "event", id="event"),
        pytest.param("event-based", "event", id="event-hyphen"),
        pytest.param("event_based", "event", id="event-underscore"),
        pytest.param("event based", "event", id="event-space"),
        pytest.param("eventual", "event", id="eventual-backward-compatible"),
        pytest.param("bernoulli", "event", id="bernoulli"),
        pytest.param("bernoulli-event", "event", id="bernoulli-event"),
        pytest.param("bernoulli_event", "event", id="bernoulli-event-underscore"),
    ],
)
def test_distribution_names_and_aliases_are_normalized(
    distribution_name: str,
    canonical_name: str,
) -> None:
    item = _make_item(distribution_name)

    assert item.distribution == canonical_name


@pytest.mark.parametrize(
    ("item", "expected_type"),
    [
        pytest.param(
            RiskItem("Triangular", "triangular", minimum=1, most_likely=2, maximum=4),
            TriangularDistribution,
            id="triangular",
        ),
        pytest.param(
            RiskItem(
                "PERT",
                "beta-pert",
                minimum=1,
                most_likely=2,
                maximum=4,
                lambda_shape=7,
            ),
            PertDistribution,
            id="pert",
        ),
        pytest.param(
            RiskItem("Uniform", "uniform", minimum=1, maximum=4),
            UniformDistribution,
            id="uniform",
        ),
        pytest.param(
            RiskItem("Normal", "normal", mean=-1, standard_deviation=2),
            NormalDistribution,
            id="normal",
        ),
        pytest.param(
            RiskItem("Log-normal", "lognormal", mean=4, standard_deviation=2),
            LogNormalDistribution,
            id="lognormal",
        ),
        pytest.param(
            RiskItem("Event", "bernoulli", probability=0.2, impact=-10),
            EventDistribution,
            id="event",
        ),
    ],
)
def test_factory_registry_builds_every_supported_distribution(
    item: RiskItem,
    expected_type: type,
) -> None:
    distribution = build_distribution(item)

    assert isinstance(distribution, expected_type)


def test_factory_propagates_custom_pert_lambda() -> None:
    item = RiskItem(
        "PERT",
        "pert",
        minimum=10,
        most_likely=20,
        maximum=40,
        lambda_shape=9.5,
    )

    distribution = build_distribution(item)

    assert isinstance(distribution, PertDistribution)
    assert distribution.lambda_shape == 9.5


def test_factory_defensively_rejects_a_mutated_distribution_name() -> None:
    item = RiskItem("Uniform", "uniform", minimum=0, maximum=1)
    item.distribution = "unknown"

    with pytest.raises(ValidationError, match="Unsupported distribution"):
        build_distribution(item)


def test_factory_defensively_rejects_a_missing_parameter_after_mutation() -> None:
    item = RiskItem("Uniform", "uniform", minimum=0, maximum=1)
    item.maximum = None

    with pytest.raises(ValidationError, match="requires parameter 'maximum'"):
        build_distribution(item)


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda: RiskItem("T", "triangular", minimum=0, maximum=1), id="triangular"),
        pytest.param(lambda: RiskItem("P", "pert", minimum=0, maximum=1), id="pert"),
        pytest.param(lambda: RiskItem("U", "uniform", minimum=0), id="uniform"),
        pytest.param(lambda: RiskItem("N", "normal", mean=0), id="normal"),
        pytest.param(lambda: RiskItem("L", "lognormal", mean=1), id="lognormal"),
        pytest.param(lambda: RiskItem("E", "event", probability=0.5), id="event"),
    ],
)
def test_required_distribution_parameters_are_enforced(
    factory: Callable[[], RiskItem],
) -> None:
    with pytest.raises(ValidationError, match="requires"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(
            lambda: RiskItem(
                "T",
                "triangular",
                minimum=math.nan,
                most_likely=0,
                maximum=1,
            ),
            id="triangular-nan",
        ),
        pytest.param(
            lambda: RiskItem(
                "P",
                "pert",
                minimum=0,
                most_likely=0.5,
                maximum=1,
                lambda_shape=math.inf,
            ),
            id="pert-infinite-lambda",
        ),
        pytest.param(
            lambda: RiskItem("U", "uniform", minimum="zero", maximum=1),
            id="uniform-string",
        ),
        pytest.param(
            lambda: RiskItem("N", "normal", mean=0, standard_deviation=True),
            id="normal-bool",
        ),
        pytest.param(
            lambda: RiskItem("L", "lognormal", mean=1j, standard_deviation=1),
            id="lognormal-complex",
        ),
        pytest.param(
            lambda: RiskItem("E", "event", probability=0.5, impact=math.inf),
            id="event-infinite-impact",
        ),
    ],
)
def test_non_finite_and_non_numeric_item_parameters_are_rejected(
    factory: Callable[[], RiskItem],
) -> None:
    with pytest.raises(ValidationError, match="finite real number"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(
            lambda: RiskItem("T", "triangular", minimum=2, most_likely=1, maximum=3),
            id="triangular-order",
        ),
        pytest.param(
            lambda: RiskItem("P", "pert", minimum=0, most_likely=0.5, maximum=1, lambda_shape=0),
            id="pert-lambda",
        ),
        pytest.param(
            lambda: RiskItem("U", "uniform", minimum=2, maximum=1),
            id="uniform-order",
        ),
        pytest.param(
            lambda: RiskItem("N", "normal", mean=0, standard_deviation=-1),
            id="normal-standard-deviation",
        ),
        pytest.param(
            lambda: RiskItem("L", "lognormal", mean=0, standard_deviation=1),
            id="lognormal-mean",
        ),
        pytest.param(
            lambda: RiskItem("E", "event", probability=1.1, impact=1),
            id="event-probability",
        ),
    ],
)
def test_invalid_item_parameter_domains_are_rejected(
    factory: Callable[[], RiskItem],
) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_negative_values_are_retained_when_mathematically_valid() -> None:
    items = [
        RiskItem("T", "triangular", minimum=-3, most_likely=-2, maximum=-1),
        RiskItem("P", "pert", minimum=-3, most_likely=-2, maximum=-1),
        RiskItem("U", "uniform", minimum=-3, maximum=-1),
        RiskItem("N", "normal", mean=-3, standard_deviation=1),
        RiskItem("E", "event", probability=0.5, impact=-3),
    ]

    assert all(build_distribution(item) for item in items)


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda: RiskItem("", "uniform", minimum=0, maximum=1), id="empty-name"),
        pytest.param(lambda: RiskItem("   ", "uniform", minimum=0, maximum=1), id="blank-name"),
        pytest.param(lambda: RiskItem(7, "uniform", minimum=0, maximum=1), id="non-string-name"),
        pytest.param(lambda: RiskItem("X", 7, minimum=0, maximum=1), id="non-string-distribution"),
        pytest.param(
            lambda: RiskItem("X", "unknown", minimum=0, maximum=1),
            id="unsupported-distribution",
        ),
    ],
)
def test_invalid_names_and_distribution_identifiers_are_rejected(
    factory: Callable[[], RiskItem],
) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_item_names_are_trimmed_and_numeric_parameters_are_normalized() -> None:
    item = RiskItem("  Estimate  ", "uniform", minimum=1, maximum=2)

    assert item.name == "Estimate"
    assert item.minimum == 1.0
    assert item.maximum == 2.0
