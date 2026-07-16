import ast
import inspect
import math
import textwrap
from collections.abc import Callable

import numpy as np
import pytest

from monte_carlo_simulator.distributions import (
    BaseDistribution,
    EventDistribution,
    LogNormalDistribution,
    NormalDistribution,
    PertDistribution,
    TriangularDistribution,
    UniformDistribution,
)
from monte_carlo_simulator.exceptions import ValidationError

DistributionFactory = Callable[[], BaseDistribution]


@pytest.mark.parametrize(
    ("distribution", "expected_mean", "expected_std"),
    [
        pytest.param(
            TriangularDistribution(minimum=10, most_likely=20, maximum=40),
            70 / 3,
            math.sqrt((10**2 + 20**2 + 40**2 - 10 * 20 - 10 * 40 - 20 * 40) / 18),
            id="triangular",
        ),
        pytest.param(
            PertDistribution(
                minimum=10,
                most_likely=20,
                maximum=40,
                lambda_shape=8,
            ),
            21,
            math.sqrt(30**2 * (11 / 3) * (19 / 3) / ((10**2) * 11)),
            id="pert-custom-lambda",
        ),
        pytest.param(
            UniformDistribution(minimum=-5, maximum=15),
            5,
            20 / math.sqrt(12),
            id="uniform",
        ),
        pytest.param(
            NormalDistribution(mean=-10, standard_deviation=7),
            -10,
            7,
            id="normal-negative-mean",
        ),
        pytest.param(
            LogNormalDistribution(mean=100, standard_deviation=25),
            100,
            25,
            id="lognormal-arithmetic-moments",
        ),
        pytest.param(
            EventDistribution(probability=0.25, impact=-40),
            -10,
            40 * math.sqrt(0.25 * 0.75),
            id="event-negative-impact",
        ),
    ],
)
def test_empirical_moments_match_theoretical_values(
    distribution: BaseDistribution,
    expected_mean: float,
    expected_std: float,
) -> None:
    sample_size = 200_000
    samples = distribution.sample(np.random.default_rng(2026), sample_size)
    mean_tolerance = 6 * expected_std / math.sqrt(sample_size)

    assert float(np.mean(samples)) == pytest.approx(expected_mean, abs=mean_tolerance)
    assert float(np.std(samples)) == pytest.approx(expected_std, rel=0.02)


@pytest.mark.parametrize(
    ("distribution", "minimum", "maximum"),
    [
        pytest.param(TriangularDistribution(-3, -1, 4), -3, 4, id="triangular"),
        pytest.param(PertDistribution(-3, -1, 4, 2.5), -3, 4, id="pert"),
        pytest.param(UniformDistribution(-3, 4), -3, 4, id="uniform"),
    ],
)
def test_bounded_distributions_stay_within_their_bounds(
    distribution: BaseDistribution,
    minimum: float,
    maximum: float,
) -> None:
    samples = distribution.sample(np.random.default_rng(31), 50_000)

    assert np.all(samples >= minimum)
    assert np.all(samples <= maximum)


@pytest.mark.parametrize(
    "distribution",
    [
        pytest.param(TriangularDistribution(1, 1, 4), id="triangular-mode-at-minimum"),
        pytest.param(TriangularDistribution(1, 4, 4), id="triangular-mode-at-maximum"),
        pytest.param(PertDistribution(1, 1, 4), id="pert-mode-at-minimum"),
        pytest.param(PertDistribution(1, 4, 4), id="pert-mode-at-maximum"),
    ],
)
def test_boundary_modes_are_supported(distribution: BaseDistribution) -> None:
    samples = distribution.sample(np.random.default_rng(8), 10_000)

    assert np.all(samples >= 1)
    assert np.all(samples <= 4)


def test_pert_shape_parameters_use_mode_and_configurable_lambda() -> None:
    distribution = PertDistribution(
        minimum=10,
        most_likely=25,
        maximum=40,
        lambda_shape=7.5,
    )

    alpha, beta = distribution._shape_parameters()

    assert alpha == pytest.approx(1 + 7.5 * (25 - 10) / (40 - 10))
    assert beta == pytest.approx(1 + 7.5 * (40 - 25) / (40 - 10))


def test_pert_shape_parameters_remain_finite_for_extreme_finite_bounds() -> None:
    distribution = PertDistribution(
        minimum=-1e308,
        most_likely=0,
        maximum=1e308,
        lambda_shape=4,
    )

    alpha, beta = distribution._shape_parameters()
    samples = distribution.sample(np.random.default_rng(7), 1_000)

    assert (alpha, beta) == pytest.approx((3, 3))
    assert np.all(np.isfinite(samples))
    assert np.all(samples >= distribution.minimum)
    assert np.all(samples <= distribution.maximum)


def test_triangular_samples_remain_finite_for_extreme_finite_bounds() -> None:
    distribution = TriangularDistribution(
        minimum=-1e308,
        most_likely=0,
        maximum=1e308,
    )

    samples = distribution.sample(np.random.default_rng(7), 1_000)

    assert np.all(np.isfinite(samples))
    assert np.all(samples >= distribution.minimum)
    assert np.all(samples <= distribution.maximum)


def test_uniform_samples_remain_finite_for_extreme_finite_bounds() -> None:
    distribution = UniformDistribution(minimum=-1e308, maximum=1e308)

    samples = distribution.sample(np.random.default_rng(7), 1_000)

    assert np.all(np.isfinite(samples))
    assert np.all(samples >= distribution.minimum)
    assert np.all(samples <= distribution.maximum)


def test_lognormal_conversion_recovers_arithmetic_moments() -> None:
    distribution = LogNormalDistribution(mean=100, standard_deviation=25)

    log_mean, log_standard_deviation = distribution._log_space_parameters()
    log_variance = log_standard_deviation**2
    recovered_mean = math.exp(log_mean + 0.5 * log_variance)
    recovered_variance = (math.exp(log_variance) - 1) * math.exp(2 * log_mean + log_variance)

    assert log_variance == pytest.approx(math.log1p((25 / 100) ** 2))
    assert recovered_mean == pytest.approx(100)
    assert math.sqrt(recovered_variance) == pytest.approx(25)


def test_lognormal_conversion_avoids_ratio_overflow() -> None:
    distribution = LogNormalDistribution(mean=1e-300, standard_deviation=1e300)

    log_mean, log_standard_deviation = distribution._log_space_parameters()

    assert math.isfinite(log_mean)
    assert math.isfinite(log_standard_deviation)


def test_lognormal_samples_are_strictly_positive() -> None:
    samples = LogNormalDistribution(50, 10).sample(np.random.default_rng(44), 50_000)

    assert np.all(samples > 0)


@pytest.mark.parametrize(
    ("distribution", "expected"),
    [
        pytest.param(TriangularDistribution(3, 3, 3), 3, id="triangular"),
        pytest.param(PertDistribution(3, 3, 3), 3, id="pert"),
        pytest.param(UniformDistribution(3, 3), 3, id="uniform"),
        pytest.param(NormalDistribution(3, 0), 3, id="normal-zero-std"),
        pytest.param(LogNormalDistribution(3, 0), 3, id="lognormal-zero-std"),
        pytest.param(EventDistribution(0, -7), 0, id="event-probability-zero"),
        pytest.param(EventDistribution(1, -7), -7, id="event-probability-one"),
        pytest.param(EventDistribution(0.4, 0), 0, id="event-zero-impact"),
    ],
)
def test_degenerate_distributions_return_constants_without_consuming_rng(
    distribution: BaseDistribution,
    expected: float,
) -> None:
    rng_after_sample = np.random.default_rng(99)
    untouched_rng = np.random.default_rng(99)

    samples = distribution.sample(rng_after_sample, 25)

    assert np.array_equal(samples, np.full(25, expected, dtype=float))
    assert rng_after_sample.random() == untouched_rng.random()


def test_event_samples_are_exactly_zero_or_impact() -> None:
    distribution = EventDistribution(probability=0.3, impact=-80)

    samples = distribution.sample(np.random.default_rng(15), 50_000)

    assert set(np.unique(samples)) == {-80.0, 0.0}


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda: TriangularDistribution(math.nan, 0, 1), id="triangular-nan"),
        pytest.param(lambda: PertDistribution(0, 0.5, 1, math.inf), id="pert-infinite"),
        pytest.param(lambda: UniformDistribution("zero", 1), id="uniform-string"),
        pytest.param(lambda: NormalDistribution(0, 1j), id="normal-complex"),
        pytest.param(lambda: LogNormalDistribution(True, 1), id="lognormal-bool"),
        pytest.param(lambda: EventDistribution(0.5, None), id="event-none"),
    ],
)
def test_non_finite_and_non_real_parameters_are_rejected(
    factory: DistributionFactory,
) -> None:
    with pytest.raises(ValidationError, match="finite real number"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda: TriangularDistribution(2, 1, 3), id="triangular-order"),
        pytest.param(lambda: PertDistribution(0, 2, 1), id="pert-order"),
        pytest.param(lambda: PertDistribution(0, 0.5, 1, 0), id="pert-zero-lambda"),
        pytest.param(lambda: PertDistribution(0, 0.5, 1, -1), id="pert-negative-lambda"),
        pytest.param(lambda: UniformDistribution(2, 1), id="uniform-order"),
        pytest.param(lambda: NormalDistribution(0, -1), id="normal-negative-std"),
        pytest.param(lambda: LogNormalDistribution(0, 1), id="lognormal-zero-mean"),
        pytest.param(lambda: LogNormalDistribution(-1, 1), id="lognormal-negative-mean"),
        pytest.param(lambda: LogNormalDistribution(1, -1), id="lognormal-negative-std"),
        pytest.param(lambda: EventDistribution(-0.01, 1), id="event-probability-below-zero"),
        pytest.param(lambda: EventDistribution(1.01, 1), id="event-probability-above-one"),
    ],
)
def test_mathematically_invalid_parameters_are_rejected(
    factory: DistributionFactory,
) -> None:
    with pytest.raises(ValidationError):
        factory()


@pytest.mark.parametrize(
    "distribution",
    [
        pytest.param(TriangularDistribution(-5, -2, 1), id="triangular"),
        pytest.param(PertDistribution(-5, -2, 1), id="pert"),
        pytest.param(UniformDistribution(-5, -1), id="uniform"),
        pytest.param(NormalDistribution(-5, 1), id="normal"),
        pytest.param(EventDistribution(0.5, -5), id="event"),
    ],
)
def test_mathematically_valid_negative_values_are_supported(
    distribution: BaseDistribution,
) -> None:
    samples = distribution.sample(np.random.default_rng(23), 100)

    assert np.all(np.isfinite(samples))


@pytest.mark.parametrize(
    "distribution",
    [
        pytest.param(TriangularDistribution(0, 0.5, 1), id="triangular"),
        pytest.param(PertDistribution(0, 0.5, 1), id="pert"),
        pytest.param(UniformDistribution(0, 1), id="uniform"),
        pytest.param(NormalDistribution(0, 1), id="normal"),
        pytest.param(LogNormalDistribution(1, 0.2), id="lognormal"),
        pytest.param(EventDistribution(0.2, 1), id="event"),
    ],
)
@pytest.mark.parametrize("invalid_size", [0, -1, 1.5, True, "10", None])
def test_invalid_sample_sizes_are_rejected(
    distribution: BaseDistribution,
    invalid_size: object,
) -> None:
    with pytest.raises(ValidationError, match="strictly positive integer"):
        distribution.sample(np.random.default_rng(2), invalid_size)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "distribution",
    [
        pytest.param(TriangularDistribution(0, 0.5, 1), id="triangular"),
        pytest.param(PertDistribution(0, 0.5, 1, 6), id="pert"),
        pytest.param(UniformDistribution(0, 1), id="uniform"),
        pytest.param(NormalDistribution(0, 1), id="normal"),
        pytest.param(LogNormalDistribution(1, 0.2), id="lognormal"),
        pytest.param(EventDistribution(0.2, -1), id="event"),
    ],
)
def test_sampling_is_reproducible_with_numpy_generators(
    distribution: BaseDistribution,
) -> None:
    first = distribution.sample(np.random.default_rng(1234), 1_000)
    second = distribution.sample(np.random.default_rng(1234), 1_000)

    assert np.array_equal(first, second)


@pytest.mark.parametrize(
    "distribution_class",
    [
        TriangularDistribution,
        PertDistribution,
        UniformDistribution,
        NormalDistribution,
        LogNormalDistribution,
        EventDistribution,
    ],
)
def test_sample_implementations_have_no_python_draw_loops(
    distribution_class: type[BaseDistribution],
) -> None:
    syntax_tree = ast.parse(textwrap.dedent(inspect.getsource(distribution_class.sample)))

    assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(syntax_tree))
