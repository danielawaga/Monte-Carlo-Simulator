# ruff: noqa: E501
"""Run an auditable end-to-end functional validation of Monte-Carlo-Simulator."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy.stats import spearmanr

from monte_carlo_simulator.analysis import compute_spearman_sensitivity
from monte_carlo_simulator.application.service import run_simulation_from_excel
from monte_carlo_simulator.distributions import build_distribution
from monte_carlo_simulator.engine import MonteCarloSimulator
from monte_carlo_simulator.exceptions import RiskRegisterValidationError
from monte_carlo_simulator.io import load_risk_register
from monte_carlo_simulator.models import RiskItem, SimulationConfig
from monte_carlo_simulator.visualization.s_curve import compute_s_curve_data

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "functional_validation"
FIXTURES = OUT / "invalid_fixtures"
REFERENCE = ROOT / "output" / "registre_risques_batiment_correlations.xlsx"
VARIANTS = {
    "V1": ROOT / "output" / "registre_risques_batiment_synthetique.xlsx",
    "V2": REFERENCE,
    "V3": ROOT / "output" / "registre_risques_batiment_stress.xlsx",
}
RESULT_DIRS = {
    "V1": ROOT / "output" / "simulation_batiment",
    "V2": ROOT / "output" / "simulation_batiment_correlations",
    "V3": ROOT / "output" / "simulation_batiment_stress",
}


class Recorder:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def check(self, family: str, test: str, passed: bool, observed: object, criterion: str) -> None:
        self.rows.append(
            {
                "family": family,
                "test": test,
                "status": "PASS" if passed else "FAIL",
                "observed": str(observed),
                "criterion": criterion,
            }
        )

    def require_all(self) -> None:
        failures = [row for row in self.rows if row["status"] == "FAIL"]
        if failures:
            raise AssertionError(f"Functional validation failures: {failures}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distribution_checks(rec: Recorder) -> None:
    size = 200_000
    cases = [
        (RiskItem("triangular", "triangular", minimum=10, most_likely=20, maximum=40), 101),
        (RiskItem("pert", "pert", minimum=10, most_likely=20, maximum=40), 102),
        (RiskItem("uniform", "uniform", minimum=10, maximum=40), 103),
        (RiskItem("normal", "normal", mean=100, standard_deviation=15), 104),
        (RiskItem("lognormal", "lognormal", mean=100, standard_deviation=20), 105),
        (RiskItem("event", "event", probability=0.23, impact=500), 106),
    ]
    records = []
    for item, seed in cases:
        values = build_distribution(item).sample(np.random.default_rng(seed), size)
        records.append(
            {
                "distribution": item.distribution,
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "mean": float(values.mean()),
                "standard_deviation": float(values.std(ddof=0)),
                "q25": float(np.quantile(values, 0.25)),
                "q50": float(np.quantile(values, 0.50)),
                "q75": float(np.quantile(values, 0.75)),
            }
        )
        if item.distribution in {"triangular", "pert", "uniform"}:
            rec.check(
                "Distributions",
                f"{item.distribution}: bornes",
                bool(np.all((values >= 10) & (values <= 40))),
                f"[{values.min():.4f}, {values.max():.4f}]",
                "Tous les tirages dans [10, 40]",
            )
        if item.distribution == "uniform":
            rec.check(
                "Distributions",
                "uniform: moyenne",
                abs(values.mean() - 25) < 0.10,
                f"{values.mean():.4f}",
                "|moyenne - 25| < 0,10",
            )
            rec.check(
                "Distributions",
                "uniform: quartiles",
                max(abs(np.quantile(values, [0.25, 0.5, 0.75]) - [17.5, 25, 32.5])) < 0.12,
                np.quantile(values, [0.25, 0.5, 0.75]).round(4).tolist(),
                "Erreur maximale des quartiles < 0,12",
            )
        if item.distribution == "normal":
            rec.check(
                "Distributions",
                "normal: moyenne",
                abs(values.mean() - 100) < 0.15,
                f"{values.mean():.4f}",
                "|moyenne - 100| < 0,15",
            )
            rec.check(
                "Distributions",
                "normal: écart-type",
                abs(values.std() - 15) < 0.15,
                f"{values.std():.4f}",
                "|écart-type - 15| < 0,15",
            )
        if item.distribution == "lognormal":
            skew_proxy = (values.mean() - np.median(values)) / values.std()
            rec.check(
                "Distributions",
                "lognormal: positivité",
                bool(np.all(values > 0)),
                f"minimum={values.min():.4f}",
                "Tous les tirages strictement positifs",
            )
            rec.check(
                "Distributions",
                "lognormal: moments",
                abs(values.mean() - 100) < 0.25 and abs(values.std() - 20) < 0.25,
                f"moyenne={values.mean():.4f}; écart-type={values.std():.4f}",
                "Erreurs absolues < 0,25",
            )
            rec.check(
                "Distributions",
                "lognormal: asymétrie",
                skew_proxy > 0.08,
                f"proxy={skew_proxy:.4f}",
                "(moyenne - médiane) / écart-type > 0,08",
            )
        if item.distribution == "event":
            frequency = float(np.mean(values == 500))
            rec.check(
                "Distributions",
                "event: valeurs possibles",
                set(np.unique(values)) == {0.0, 500.0},
                sorted(np.unique(values).tolist()),
                "Valeurs exactement {0, impact}",
            )
            rec.check(
                "Distributions",
                "event: fréquence",
                abs(frequency - 0.23) < 0.003,
                f"{frequency:.5f}",
                "|fréquence - 0,23| < 0,003",
            )
    pd.DataFrame(records).to_csv(OUT / "distribution_checks.csv", index=False)


def reproducibility_checks(rec: Recorder) -> None:
    config = SimulationConfig(number_of_simulations=10_000, random_seed=42)
    runs = []
    for label in ("same_seed_a", "same_seed_b"):
        target = OUT / label
        run = run_simulation_from_excel(REFERENCE, config, target)
        runs.append(run)
    same_samples = np.array_equal(runs[0].result.samples, runs[1].result.samples)
    same_items = runs[0].result.item_samples.equals(runs[1].result.item_samples)
    csv_names = ["simulation_summary.csv", "sensitivity_summary.csv", "baseline_comparison.csv"]
    hashes_a = {name: sha256(OUT / "same_seed_a" / name) for name in csv_names}
    hashes_b = {name: sha256(OUT / "same_seed_b" / name) for name in csv_names}
    rec.check(
        "Reproductibilité",
        "tirages identiques",
        same_samples and same_items,
        f"totaux={same_samples}; postes={same_items}",
        "Égalité bit à bit avec même graine",
    )
    rec.check(
        "Reproductibilité",
        "CSV identiques",
        hashes_a == hashes_b,
        hashes_a,
        "SHA-256 identiques pour les trois CSV",
    )

    other = run_simulation_from_excel(
        REFERENCE,
        SimulationConfig(number_of_simulations=10_000, random_seed=43),
        OUT / "other_seed",
    )
    changed = not np.array_equal(runs[0].result.samples, other.result.samples)
    relative_mean_gap = (
        abs(runs[0].result.samples.mean() - other.result.samples.mean())
        / runs[0].result.samples.mean()
    )
    relative_p90_gap = abs(
        np.quantile(runs[0].result.samples, 0.9) - np.quantile(other.result.samples, 0.9)
    ) / np.quantile(runs[0].result.samples, 0.9)
    rec.check(
        "Reproductibilité",
        "autre graine: tirages différents",
        changed,
        changed,
        "Les tableaux de tirages diffèrent",
    )
    rec.check(
        "Reproductibilité",
        "autre graine: stabilité statistique",
        relative_mean_gap < 0.003 and relative_p90_gap < 0.005,
        f"écart moyen={relative_mean_gap:.5%}; écart P90={relative_p90_gap:.5%}",
        "Écart moyen < 0,3 % et écart P90 < 0,5 %",
    )


def correlation_checks(rec: Recorder) -> None:
    register = load_risk_register(REFERENCE)
    result = MonteCarloSimulator().run(
        register.items,
        SimulationConfig(number_of_simulations=200_000, random_seed=4242),
        correlation_matrix=register.correlation_matrix,
    )
    samples = result.item_samples
    assert samples is not None and register.correlation_matrix is not None
    matrix = register.correlation_matrix.values
    names = list(register.correlation_matrix.item_names)
    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            target = float(matrix[i, j])
            if target == 0:
                continue
            observed = float(spearmanr(samples[names[i]], samples[names[j]]).statistic)
            rows.append(
                {
                    "first": names[i],
                    "second": names[j],
                    "target": target,
                    "observed_spearman": observed,
                    "absolute_error": abs(observed - target),
                }
            )
            involves_event = (
                register.items[i].distribution == "event"
                or register.items[j].distribution == "event"
            )
            passed = (
                (observed > 0.20 and observed < target)
                if involves_event
                else (np.sign(observed) == np.sign(target) and abs(observed - target) < 0.05)
            )
            criterion = (
                "Événement discret : 0,20 < Spearman observé < corrélation latente"
                if involves_event
                else "Même signe et écart absolu < 0,05"
            )
            rec.check(
                "Corrélations",
                f"{names[i]} / {names[j]}",
                passed,
                f"cible latente={target:.2f}; Spearman observé={observed:.4f}",
                criterion,
            )
    pd.DataFrame(rows).to_csv(OUT / "correlation_checks.csv", index=False)
    zero_pairs = [(names[0], names[8]), (names[5], names[10]), (names[15], names[17])]
    for first, second in zero_pairs:
        observed = float(spearmanr(samples[first], samples[second]).statistic)
        rec.check(
            "Corrélations",
            f"absence imposée: {first} / {second}",
            abs(observed) < 0.015,
            f"Spearman={observed:.4f}",
            "|Spearman| < 0,015",
        )


def variant_checks(rec: Recorder) -> None:
    summaries = {
        key: pd.read_csv(path / "simulation_summary.csv").iloc[0]
        for key, path in RESULT_DIRS.items()
    }
    baselines = {
        key: pd.read_csv(path / "baseline_comparison.csv").iloc[0]
        for key, path in RESULT_DIRS.items()
    }
    rec.check(
        "Variantes",
        "V2: moyenne stable",
        abs(summaries["V2"]["mean"] - summaries["V1"]["mean"]) / summaries["V1"]["mean"] < 0.001,
        f"V1={summaries['V1']['mean']:.0f}; V2={summaries['V2']['mean']:.0f}",
        "Écart relatif < 0,1 %",
    )
    rec.check(
        "Variantes",
        "V2: dispersion accrue",
        summaries["V2"]["std"] > summaries["V1"]["std"]
        and summaries["V2"]["P90"] > summaries["V1"]["P90"],
        f"std +{summaries['V2']['std'] / summaries['V1']['std'] - 1:.1%}; P90 +{summaries['V2']['P90'] - summaries['V1']['P90']:.0f}",
        "Écart-type et P90 supérieurs",
    )
    rec.check(
        "Variantes",
        "V3: déplacement défavorable",
        all(
            summaries["V3"][field] > summaries["V2"][field]
            for field in ("mean", "median", "std", "P80", "P90")
        ),
        {
            field: float(summaries["V3"][field] - summaries["V2"][field])
            for field in ("mean", "median", "std", "P80", "P90")
        },
        "Moyenne, médiane, écart-type, P80 et P90 supérieurs",
    )
    rec.check(
        "Variantes",
        "V3: baseline davantage dépassée",
        baselines["V3"]["exceedance_probability"] > baselines["V2"]["exceedance_probability"],
        f"V2={baselines['V2']['exceedance_probability']:.2%}; V3={baselines['V3']['exceedance_probability']:.2%}",
        "Probabilité V3 > probabilité V2",
    )


def invalid_workbook_checks(rec: Recorder) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    cases = {
        "minimum_superieur_maximum": lambda w: setattr(w["risk_register"]["C4"], "value", 900_000),
        "probabilite_superieure_1": lambda w: setattr(w["risk_register"]["H14"], "value", 1.20),
        "distribution_inconnue": lambda w: setattr(w["risk_register"]["B2"], "value", "mystery"),
        "parametre_obligatoire_manquant": lambda w: setattr(
            w["risk_register"]["E4"], "value", None
        ),
        "matrice_non_symetrique": lambda w: setattr(w["correlations"]["E3"], "value", 0.20),
        "diagonale_differente_1": lambda w: setattr(w["correlations"]["B2"], "value", 0.90),
        "nom_poste_duplique": lambda w: setattr(
            w["risk_register"]["A3"], "value", w["risk_register"]["A2"].value
        ),
        "unites_incompatibles": lambda w: setattr(w["risk_register"]["L2"], "value", "EUR"),
    }

    def non_pd(workbook):
        sheet = workbook["correlations"]
        for a, b, value in (("C2", "B3", 0.9), ("D2", "B4", 0.9), ("D3", "C4", -0.9)):
            sheet[a] = value
            sheet[b] = value

    cases["matrice_non_definie_positive"] = non_pd

    messages = []
    for name, mutate in cases.items():
        path = FIXTURES / f"{name}.xlsx"
        shutil.copy2(REFERENCE, path)
        workbook = load_workbook(path)
        mutate(workbook)
        workbook.save(path)
        workbook.close()
        try:
            load_risk_register(path)
        except RiskRegisterValidationError as exc:
            message = str(exc).replace("\n", " | ")
            messages.append({"case": name, "rejected": True, "message": message})
            rec.check(
                "Erreurs Excel",
                name,
                True,
                message[:220],
                "Fichier rejeté avec contexte utilisateur",
            )
        else:
            messages.append({"case": name, "rejected": False, "message": ""})
            rec.check(
                "Erreurs Excel", name, False, "accepté", "Fichier rejeté avec contexte utilisateur"
            )
    pd.DataFrame(messages).to_csv(OUT / "invalid_workbook_checks.csv", index=False)


def independent_output_checks(rec: Recorder) -> None:
    run = run_simulation_from_excel(
        REFERENCE,
        SimulationConfig(number_of_simulations=10_000, random_seed=42),
        OUT / "independent_recalculation",
    )
    samples = run.result.samples
    items = run.result.item_samples
    assert items is not None
    saved_summary = pd.read_csv(run.summary_path).iloc[0]
    independent = {
        "mean": float(np.mean(samples)),
        "median": float(np.median(samples)),
        "std": float(np.std(samples, ddof=0)),
        "minimum": float(np.min(samples)),
        "maximum": float(np.max(samples)),
        "P50": float(np.quantile(samples, 0.5)),
        "P80": float(np.quantile(samples, 0.8)),
        "P90": float(np.quantile(samples, 0.9)),
    }
    summary_ok = all(
        np.isclose(saved_summary[key], value, rtol=0, atol=1e-9)
        for key, value in independent.items()
    )
    rec.check("Sorties", "résumé recalculé", summary_ok, independent, "Égalité numérique à 1e-9")

    baseline = 7_750_000.0
    saved_base = pd.read_csv(run.baseline_comparison_path).iloc[0]
    frequency = float(np.mean(samples > baseline))
    percentile_map = {"p50": "P50", "p80": "P80", "p90": "P90"}
    base_ok = np.isclose(saved_base["exceedance_probability"], frequency, atol=1e-12) and all(
        np.isclose(saved_base[csv_label], independent[summary_label], atol=1e-9)
        for csv_label, summary_label in percentile_map.items()
    )
    rec.check(
        "Sorties",
        "baseline recalculée",
        base_ok,
        f"fréquence={frequency:.6f}; CSV={saved_base['exceedance_probability']:.6f}",
        "Fréquence stricte et quantiles identiques",
    )

    saved_sens = pd.read_csv(run.sensitivity_path).set_index("item_name")
    independent_sens = compute_spearman_sensitivity(items, samples).set_index("item_name")
    sens_ok = np.allclose(
        saved_sens.loc[independent_sens.index, "spearman_rho"],
        independent_sens["spearman_rho"],
        equal_nan=True,
        atol=1e-12,
    )
    order_ok = saved_sens["absolute_rho"].is_monotonic_decreasing and saved_sens[
        "rank"
    ].tolist() == list(range(1, len(saved_sens) + 1))
    rec.check(
        "Sorties",
        "sensibilité Spearman recalculée",
        sens_ok and order_ok,
        f"coefficients={sens_ok}; classement={order_ok}",
        "Coefficients identiques, |rho| décroissant et rangs consécutifs",
    )
    additivity = np.allclose(items.sum(axis=1).to_numpy(), samples, rtol=0, atol=1e-8)
    rec.check(
        "Sorties",
        "total sans double comptage",
        additivity,
        f"écart max={np.max(np.abs(items.sum(axis=1).to_numpy() - samples)):.3e}",
        "Somme des contributions = total simulé",
    )

    decision = pd.read_csv(run.percentile_table_path)
    expected_levels = np.array([0.50, 0.80, 0.90])
    expected_amounts = np.quantile(samples, expected_levels)
    decision_ok = (
        np.allclose(decision["confidence_level"], expected_levels, atol=0, rtol=0)
        and np.allclose(decision["amount"], expected_amounts, atol=1e-9, rtol=0)
        and np.allclose(decision["probability_of_exceedance"], 1 - expected_levels, atol=1e-12)
        and np.allclose(decision["gap_to_baseline"], expected_amounts - baseline, atol=1e-9)
        and np.allclose(
            decision["recommended_reserve"], np.maximum(expected_amounts - baseline, 0), atol=1e-9
        )
    )
    rec.check(
        "Sorties",
        "table de décision recalculée",
        decision_ok,
        decision[["percentile", "amount", "recommended_reserve"]].to_dict("records"),
        "Percentiles, dépassement et réserve recalculés indépendamment",
    )

    convergence = pd.read_csv(run.convergence_path)
    draw_counts = convergence["draw_count"].to_numpy(dtype=int)
    estimates = np.array([np.quantile(samples[:count], 0.90) for count in draw_counts])
    convergence_ok = (
        draw_counts[-1] == len(samples)
        and np.all(np.diff(draw_counts) > 0)
        and np.allclose(convergence["estimate"], estimates, atol=1e-9, rtol=0)
        and convergence["stop_recommended"].sum() <= 1
    )
    rec.check(
        "Sorties",
        "convergence recalculée",
        convergence_ok,
        f"blocs={len(draw_counts)}; dernier={draw_counts[-1]}; stops={int(convergence['stop_recommended'].sum())}",
        "Comptages croissants, P90 cumulé identique et au plus un arrêt recommandé",
    )

    s_curve = compute_s_curve_data(samples)
    s_curve_ok = (
        len(s_curve) == len(samples)
        and s_curve["total"].is_monotonic_increasing
        and np.isclose(s_curve["cumulative_probability"].iloc[-1], 1.0)
        and np.all(np.diff(s_curve["cumulative_probability"]) > 0)
        and run.s_curve_path.exists()
        and run.s_curve_path.stat().st_size > 0
    )
    rec.check(
        "Sorties",
        "courbe en S cohérente",
        s_curve_ok,
        f"points={len(s_curve)}; probabilité finale={s_curve['cumulative_probability'].iloc[-1]:.6f}",
        "Totaux triés, probabilités strictement croissantes jusqu'à 1 et image non vide",
    )

    artifacts_ok = len(run.artifact_paths) == 8 and all(
        path.exists() and path.stat().st_size > 0 for path in run.artifact_paths
    )
    rec.check(
        "Sorties",
        "jeu complet de livrables",
        artifacts_ok,
        [path.name for path in run.artifact_paths],
        "Huit livrables attendus, présents et non vides",
    )


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    rec = Recorder()
    distribution_checks(rec)
    reproducibility_checks(rec)
    correlation_checks(rec)
    variant_checks(rec)
    invalid_workbook_checks(rec)
    independent_output_checks(rec)
    results = pd.DataFrame(rec.rows)
    results.to_csv(OUT / "validation_results.csv", index=False)
    summary = results.groupby(["family", "status"]).size().unstack(fill_value=0)
    summary.to_csv(OUT / "validation_summary.csv")
    payload = {
        "total_checks": len(results),
        "passed": int((results.status == "PASS").sum()),
        "failed": int((results.status == "FAIL").sum()),
        "families": {
            family: int(count) for family, count in results.groupby("family").size().items()
        },
    }
    (OUT / "validation_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    rec.require_all()


if __name__ == "__main__":
    main()
