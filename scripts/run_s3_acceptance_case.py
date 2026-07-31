"""Run a reproducible, synthetic S3 acceptance case and write an evidence report."""

from pathlib import Path

import pandas as pd

from monte_carlo_simulator.application import run_simulation_from_excel
from monte_carlo_simulator.models import SimulationConfig
from scripts.generate_correlated_cost_register import generate

REQUIRED_ARTIFACTS = (
    "simulation_histogram.png",
    "simulation_summary.csv",
    "simulation_s_curve.png",
    "percentile_decision_table.csv",
    "convergence_diagnostics.csv",
    "correlation_diagnostics.csv",
    "sensitivity_summary.csv",
    "sensitivity_tornado.png",
    "baseline_comparison.csv",
)


def run_acceptance_case(
    output_root: str | Path,
    *,
    simulations: int = 10_000,
    seed: int = 42,
) -> Path:
    """Execute the complete synthetic workflow and return the Markdown report path."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    input_path = generate(root / "synthetic_s3_acceptance_register.xlsx")
    artifact_dir = root / "artifacts"

    run = run_simulation_from_excel(
        input_path,
        SimulationConfig(
            number_of_simulations=simulations,
            random_seed=seed,
            confidence_levels=(0.50, 0.80, 0.90),
        ),
        artifact_dir,
    )

    percentile_table = pd.read_csv(run.percentile_table_path)
    convergence = pd.read_csv(run.convergence_path)
    sensitivity = pd.read_csv(run.sensitivity_path)
    if run.correlation_diagnostics_path is None:
        raise RuntimeError("The synthetic acceptance register must contain correlations.")
    correlation = pd.read_csv(run.correlation_diagnostics_path)

    amounts = percentile_table.set_index("percentile")["amount"]
    artifact_checks = {
        name: (artifact_dir / name).exists() for name in REQUIRED_ARTIFACTS
    }
    checks = {
        "requested draw count produced": len(run.result.samples) == simulations,
        "P50 <= P80 <= P90": amounts["P50"] <= amounts["P80"] <= amounts["P90"],
        "all decision artifacts generated": all(artifact_checks.values()),
        "convergence diagnostics reach final draw": int(convergence.iloc[-1]["draw_count"])
        == simulations,
        "strict positive-definite correlation accepted": bool(
            correlation.loc[0, "strictly_positive_definite"]
        ),
        "no automatic correlation repair applied": not bool(
            correlation.loc[0, "automatic_repair_applied"]
        ),
        "at least one sensitivity coefficient defined": bool(sensitivity["is_defined"].any()),
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    stable_rows = convergence.loc[convergence["stop_recommended"]]
    recommended_draws = (
        str(int(stable_rows.iloc[0]["draw_count"])) if not stable_rows.empty else "not reached"
    )
    top_sensitivity = sensitivity.loc[sensitivity["is_defined"]].head(3)
    sensitivity_lines = [
        f"- {row.item_name}: rho={row.spearman_rho:.4f}, rank={int(row.rank)}"
        for row in top_sensitivity.itertuples()
    ]

    report_lines = [
        "# S3 synthetic acceptance report",
        "",
        f"**Overall status: {overall_status}**",
        "",
        "> Synthetic and explicitly non-representative data. No client, consultant or real project data is included.",
        "",
        "## Run configuration",
        "",
        f"- Simulations: {simulations}",
        f"- Random seed: {seed}",
        f"- Input workbook: `{input_path.name}`",
        f"- Correlation policy: `{correlation.loc[0, 'policy']}`",
        f"- Minimum eigenvalue: {correlation.loc[0, 'minimum_eigenvalue']:.6g}",
        f"- Recommended convergence draw count: {recommended_draws}",
        "",
        "## Decision percentiles",
        "",
        "| Percentile | Amount | Probability of exceedance | Recommended reserve |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in percentile_table.itertuples():
        report_lines.append(
            f"| {row.percentile} | {row.amount:.4f} | "
            f"{row.probability_of_exceedance:.2%} | {row.recommended_reserve:.4f} |"
        )

    report_lines.extend(["", "## Dominant sensitivity signals", ""])
    report_lines.extend(sensitivity_lines or ["- No defined coefficient."])
    report_lines.extend(["", "## Acceptance checks", ""])
    report_lines.extend(
        f"- [{'x' if passed else ' '}] {label}" for label, passed in checks.items()
    )
    report_lines.extend(["", "## Generated artifacts", ""])
    report_lines.extend(
        f"- [{'x' if exists else ' '}] `{name}`" for name, exists in artifact_checks.items()
    )
    report_lines.extend(
        [
            "",
            "## Scope boundary",
            "",
            "This report validates the software path and numerical invariants only. "
            "Credibility of real assumptions still requires an anonymized register and consultant review.",
            "",
        ]
    )

    report_path = root / "s3_acceptance_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    path = run_acceptance_case(Path("data/output/s3_acceptance"))
    print(f"S3 acceptance report written to: {path}")
