"""Application service orchestration."""

from pathlib import Path

from monte_carlo_simulator.analysis import (
    build_percentile_decision_table,
    build_tornado_data,
    compute_baseline_comparison,
    compute_convergence_diagnostics,
    compute_spearman_sensitivity,
)
from monte_carlo_simulator.config import OUTPUT_DIR
from monte_carlo_simulator.engine import MonteCarloSimulator
from monte_carlo_simulator.exceptions import ValidationError
from monte_carlo_simulator.io import (
    export_baseline_comparison_to_csv,
    export_convergence_to_csv,
    export_percentile_table_to_csv,
    export_sensitivity_to_csv,
    export_summary_to_csv,
    load_risk_register,
)
from monte_carlo_simulator.models import (
    ExcelSimulationRun,
    RiskItem,
    SimulationConfig,
    SimulationResult,
)
from monte_carlo_simulator.visualization.histogram import save_histogram
from monte_carlo_simulator.visualization.s_curve import save_s_curve
from monte_carlo_simulator.visualization.tornado import build_tornado_chart


def create_sample_risk_items() -> list[RiskItem]:
    """Create five fictive triangular risk items."""
    return [
        RiskItem(
            "Studies",
            "triangular",
            minimum=10_000,
            most_likely=15_000,
            maximum=22_000,
            category="engineering",
            unit="EUR",
        ),
        RiskItem(
            "Development",
            "triangular",
            minimum=30_000,
            most_likely=45_000,
            maximum=70_000,
            category="engineering",
            unit="EUR",
        ),
        RiskItem(
            "Testing",
            "triangular",
            minimum=12_000,
            most_likely=20_000,
            maximum=32_000,
            category="quality",
            unit="EUR",
        ),
        RiskItem(
            "Documentation",
            "triangular",
            minimum=4_000,
            most_likely=7_000,
            maximum=12_000,
            category="management",
            unit="EUR",
        ),
        RiskItem(
            "Deployment",
            "triangular",
            minimum=8_000,
            most_likely=13_000,
            maximum=21_000,
            category="operations",
            unit="EUR",
        ),
    ]


def run_demo_simulation(
    config: SimulationConfig | None = None,
    output_dir: Path | None = None,
) -> tuple[SimulationResult, Path]:
    """Run the week-1 triangular proof of concept and save histogram."""
    simulation_config = config or SimulationConfig()
    simulator = MonteCarloSimulator()
    result = simulator.run(create_sample_risk_items(), simulation_config)

    target_dir = output_dir or OUTPUT_DIR
    histogram_path = target_dir / "triangular_histogram.png"
    save_histogram(result.samples, result.summary, histogram_path)
    return result, histogram_path


def run_simulation_from_excel(
    file_path: str | Path,
    config: SimulationConfig | None = None,
    output_dir: str | Path | None = None,
) -> ExcelSimulationRun:
    """Validate an Excel risk register, simulate it and persist its artifacts."""
    register = load_risk_register(file_path)
    simulation_config = config or SimulationConfig()
    result = MonteCarloSimulator().run(
        register.items,
        simulation_config,
        correlation_matrix=register.correlation_matrix,
    )

    target_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    histogram_path = target_dir / "simulation_histogram.png"
    summary_path = target_dir / "simulation_summary.csv"
    s_curve_path = target_dir / "simulation_s_curve.png"
    percentile_table_path = target_dir / "percentile_decision_table.csv"
    convergence_path = target_dir / "convergence_diagnostics.csv"
    sensitivity_path = target_dir / "sensitivity_summary.csv"
    tornado_path = target_dir / "sensitivity_tornado.png"
    baseline = register.metadata.baseline_estimate
    baseline_comparison_path = (
        target_dir / "baseline_comparison.csv" if baseline is not None else None
    )
    analysis_label = register.metadata.analysis_type.capitalize()
    x_label = f"Total {register.metadata.analysis_type} ({register.metadata.default_unit})"
    save_histogram(
        result.samples,
        result.summary,
        histogram_path,
        title=f"Monte Carlo Total {analysis_label} Distribution",
        x_label=x_label,
    )
    save_s_curve(
        result.samples,
        result.summary,
        s_curve_path,
        title=f"Monte Carlo Total {analysis_label} S-curve",
        x_label=x_label,
    )
    export_summary_to_csv(result.summary, summary_path)

    percentile_table = build_percentile_decision_table(
        result.samples,
        simulation_config.confidence_levels,
        baseline_estimate=baseline,
        unit=register.metadata.default_unit,
    )
    export_percentile_table_to_csv(percentile_table, percentile_table_path)

    block_size = max(1, min(1_000, simulation_config.number_of_simulations // 10))
    convergence = compute_convergence_diagnostics(
        result.samples,
        confidence_level=max(simulation_config.confidence_levels),
        block_size=block_size,
    )
    export_convergence_to_csv(convergence, convergence_path)

    if result.item_samples is None:
        raise ValidationError("Sensitivity analysis requires SimulationResult.item_samples.")
    sensitivity = compute_spearman_sensitivity(result.item_samples, result.samples)
    export_sensitivity_to_csv(sensitivity, sensitivity_path)
    tornado_data = build_tornado_data(sensitivity)
    build_tornado_chart(tornado_data, tornado_path)
    if baseline is not None and baseline_comparison_path is not None:
        comparison = compute_baseline_comparison(result.samples, baseline)
        export_baseline_comparison_to_csv(comparison, baseline_comparison_path)

    source_path = register.source_path or Path(file_path).resolve()
    return ExcelSimulationRun(
        result=result,
        metadata=register.metadata,
        histogram_path=histogram_path,
        summary_path=summary_path,
        source_path=source_path,
        sensitivity_path=sensitivity_path,
        tornado_path=tornado_path,
        baseline_comparison_path=baseline_comparison_path,
        s_curve_path=s_curve_path,
        percentile_table_path=percentile_table_path,
        convergence_path=convergence_path,
    )
