"""Build a portable ZIP report containing workbooks and chart images."""

from __future__ import annotations

import json
from collections.abc import Mapping
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from matplotlib.figure import Figure

from .results_workbook import build_simulation_results_workbook

ORANGE = "#f45116"
NAVY = "#14213d"
BLUE = "#176ee0"
GREEN = "#178342"
GRID = "#dfe5ed"


def _records(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _figure(title: str, x_label: str = "", y_label: str = "") -> tuple[Figure, Any]:
    figure = Figure(figsize=(10, 5.8), facecolor="white", constrained_layout=True)
    axis = figure.subplots()
    axis.set_title(title, loc="left", color=NAVY, fontsize=15, fontweight="bold", pad=16)
    axis.set_xlabel(x_label, color=NAVY)
    axis.set_ylabel(y_label, color=NAVY)
    axis.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    return figure, axis


def _png(figure: Figure) -> bytes:
    stream = BytesIO()
    figure.savefig(stream, format="png", dpi=160, facecolor="white")
    return stream.getvalue()


def _empty(axis: Any, message: str) -> None:
    axis.text(0.5, 0.5, message, ha="center", va="center", color=NAVY, transform=axis.transAxes)
    axis.set_xticks([])
    axis.set_yticks([])


def _histogram(result: Mapping[str, Any], unit: str) -> bytes:
    figure, axis = _figure("Distribution du résultat total", f"Valeur totale ({unit})", "Fréquence")
    records = _records(result.get("histogram"))
    bins: list[tuple[float, float, float]] = []
    for record in records:
        start = _number(record.get("start"))
        end = _number(record.get("end"))
        count = _number(record.get("count"))
        if start is not None and end is not None and count is not None:
            bins.append((start, end, count))
    if records and len(bins) == len(records):
        starts = [start for start, _, _ in bins]
        counts = [count for _, _, count in bins]
        widths = [end - start for start, end, _ in bins]
        axis.bar(starts, counts, width=widths, align="edge", color="#fff1e8", edgecolor=ORANGE)
        summary = _mapping(result.get("summary"))
        mean = _number(summary.get("mean"))
        if mean is not None:
            axis.axvline(mean, color=ORANGE, linestyle="--", linewidth=2, label="Moyenne")
        for record in _records(result.get("percentiles")):
            label = str(record.get("percentile", ""))
            if label in {"P80", "P90"} and (amount := _number(record.get("amount"))) is not None:
                axis.axvline(
                    amount,
                    color=BLUE if label == "P80" else NAVY,
                    linestyle=":",
                    linewidth=2,
                    label=label,
                )
        axis.legend(frameon=False)
    else:
        _empty(axis, "Aucune donnée d'histogramme disponible")
    return _png(figure)


def _s_curve(result: Mapping[str, Any], unit: str) -> bytes:
    figure, axis = _figure(
        "Courbe de probabilité empirique (S-curve)",
        f"Valeur totale ({unit})",
        "Probabilité cumulée (%)",
    )
    records = _records(result.get("sCurve"))
    points: list[tuple[float, float]] = []
    for record in records:
        amount = _number(record.get("amount"))
        probability = _number(record.get("probability"))
        if amount is not None and probability is not None:
            points.append((amount, probability))
    if points:
        axis.plot(
            [point[0] for point in points],
            [point[1] * 100 for point in points],
            color=ORANGE,
            linewidth=2.5,
        )
        axis.fill_between(
            [point[0] for point in points],
            [point[1] * 100 for point in points],
            color="#fff1e8",
            alpha=0.7,
        )
        axis.set_ylim(0, 100)
    else:
        _empty(axis, "Aucun point de probabilité cumulée disponible")
    return _png(figure)


def _sensitivity(result: Mapping[str, Any]) -> bytes:
    figure, axis = _figure(
        "Sensibilité des postes — coefficient de Spearman", "Coefficient de Spearman", ""
    )
    records = []
    for record in _records(result.get("sensitivity")):
        coefficient = _number(record.get("spearman_rho"))
        if coefficient is not None:
            records.append((str(record.get("item_name", "Poste")), coefficient))
    records = sorted(records, key=lambda item: abs(item[1]), reverse=True)[:10]
    if records:
        records.reverse()
        names = [item[0] for item in records]
        coefficients = [item[1] for item in records]
        axis.barh(
            names, coefficients, color=[ORANGE if value >= 0 else BLUE for value in coefficients]
        )
        axis.axvline(0, color=NAVY, linewidth=1)
        axis.set_xlim(-1, 1)
    else:
        _empty(axis, "Aucune donnée de sensibilité disponible")
    return _png(figure)


def _convergence(result: Mapping[str, Any], unit: str) -> bytes:
    figure, axis = _figure(
        "Convergence du percentile cible", "Nombre de tirages", f"Estimation ({unit})"
    )
    records = _records(result.get("convergence"))
    points: list[tuple[float, float]] = []
    for record in records:
        draws = _number(record.get("draw_count"))
        estimate = _number(record.get("estimate"))
        if draws is not None and estimate is not None:
            points.append((draws, estimate))
    if points:
        axis.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            color=ORANGE,
            marker="o",
            linewidth=2,
        )
        stable = [record for record in records if record.get("stop_recommended") is True]
        if stable:
            draws = _number(stable[0].get("draw_count"))
            estimate = _number(stable[0].get("estimate"))
            if draws is not None and estimate is not None:
                axis.scatter(
                    [draws],
                    [estimate],
                    color=GREEN,
                    s=90,
                    zorder=3,
                    label="Stabilisation recommandée",
                )
                axis.legend(frameon=False)
    else:
        _empty(axis, "Aucune donnée de convergence disponible")
    return _png(figure)


def build_simulation_results_bundle(
    *,
    result: Mapping[str, Any],
    register: Mapping[str, Any],
    config: Mapping[str, Any],
    register_workbook: bytes,
) -> bytes:
    """Return a ZIP containing the input register, results workbook and all charts."""

    project = _mapping(result.get("project"))
    unit = str(project.get("unit") or "unité")
    results_workbook = build_simulation_results_workbook(
        result=result,
        register=register,
        config=config,
    )
    charts = {
        "graphiques/01_histogramme_distribution.png": _histogram(result, unit),
        "graphiques/02_courbe_probabilite_s.png": _s_curve(result, unit),
        "graphiques/03_sensibilite_tornado.png": _sensitivity(result),
        "graphiques/04_convergence.png": _convergence(result, unit),
    }
    readme = (
        "DOSSIER DE RÉSULTATS MONTE-CARLO\n\n"
        "- registre_risques_utilise.xlsx : données d'entrée compatibles avec la plateforme.\n"
        "- resultats_monte_carlo.xlsx : synthèse, percentiles, sensibilité, "
        "convergence et hypothèses.\n"
        "- graphiques/ : quatre visualisations PNG prêtes à intégrer dans un rapport.\n"
        "- donnees/resultats.json : réponse complète du moteur pour la traçabilité.\n\n"
        "Le registre d'entrée reste séparé des résultats afin de préserver sa structure "
        "et de faciliter les réimportations.\n"
    )
    stream = BytesIO()
    with ZipFile(stream, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("LISEZ_MOI.txt", readme)
        archive.writestr("registre_risques_utilise.xlsx", register_workbook)
        archive.writestr("resultats_monte_carlo.xlsx", results_workbook)
        archive.writestr(
            "donnees/resultats.json",
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
        )
        for path, content in charts.items():
            archive.writestr(path, content)
    return stream.getvalue()
