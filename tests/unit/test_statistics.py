import numpy as np

from monte_carlo_simulator.analysis.statistics import compute_summary_statistics


def test_percentiles_are_ordered() -> None:
    rng = np.random.default_rng(42)
    samples = rng.normal(loc=100.0, scale=20.0, size=10_000)

    summary = compute_summary_statistics(samples)

    p50 = float(summary.loc[0, "P50"])
    p80 = float(summary.loc[0, "P80"])
    p90 = float(summary.loc[0, "P90"])

    assert p50 <= p80 <= p90
