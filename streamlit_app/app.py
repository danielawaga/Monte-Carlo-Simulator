"""Interactive Streamlit interface for the Monte Carlo simulator."""

from __future__ import annotations

import hashlib
import io
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from monte_carlo_simulator.application.presentation import (
    build_confidence_levels,
    build_decision_snapshot,
)
from monte_carlo_simulator.application.service import run_simulation_from_excel
from monte_carlo_simulator.exceptions import RiskRegisterValidationError, ValidationError
from monte_carlo_simulator.models import SimulationConfig

APP_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = APP_ROOT / "data" / "templates" / "risk_register_template.xlsx"

st.set_page_config(
    page_title="Monte Carlo · Project Risk",
    page_icon="◩",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
      :root {
        --mc-background-veil: linear-gradient(
          rgba(247,250,247,.52), rgba(224,237,231,.58)
        );
        --mc-chrome: rgba(255,255,255,.12);
        --mc-surface: color-mix(
          in srgb, var(--secondary-background-color, #f0f2f6) 82%, transparent
        );
        --mc-border: color-mix(in srgb, var(--text-color, #31333f) 24%, transparent);
        --mc-muted: color-mix(in srgb, var(--text-color, #31333f) 68%, transparent);
      }
      [data-theme="dark"] {
        --mc-surface: color-mix(
          in srgb, var(--secondary-background-color, #262730) 78%, transparent
        );
      }
      :root[data-mc-theme="dark"] {
        --mc-background-veil: linear-gradient(135deg,
          rgba(3,13,8,.78) 0%, rgba(5,14,9,.80) 50%, rgba(3,10,6,.82) 100%
        );
        --mc-chrome: rgba(14,24,18,.18);
      }
      :root[data-mc-theme="dark"] .hero,
      :root[data-mc-theme="dark"] .hero small,
      :root[data-mc-theme="dark"] .hero h1,
      :root[data-mc-theme="dark"] .hero p,
      :root[data-mc-theme="dark"] .st-key-run-metadata,
      :root[data-mc-theme="dark"] .st-key-run-metadata * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] .hero small {
        color: #ff9f5a !important;
      }
      :root[data-mc-theme="dark"] .st-key-method-content,
      :root[data-mc-theme="dark"] .st-key-method-content * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stHeader"],
      :root[data-mc-theme="dark"] [data-testid="stHeader"] * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stHeader"] svg {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
        color: rgba(255,255,255,.72) !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(2,5,4,.94) !important;
        border-color: rgba(93,202,165,.28) !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderDropzone"] *,
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderDropzone"] small {
        color: rgba(255,255,255,.68) !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderDropzone"] button {
        background: rgba(255,255,255,.08) !important;
        border-color: rgba(255,255,255,.22) !important;
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderFile"] {
        background: rgba(24,55,42,.94) !important;
        border: 1px solid rgba(93,202,165,.30) !important;
        border-radius: .55rem;
        padding: .5rem .65rem;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderFile"],
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderFile"] * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stFileUploaderFile"] small {
        color: rgba(255,255,255,.70) !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stMain"] .stDownloadButton button {
        background: rgba(0,0,0,.88) !important;
        border-color: rgba(255,255,255,.18) !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stMain"] .stDownloadButton button,
      :root[data-mc-theme="dark"] [data-testid="stMain"] .stDownloadButton button * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stMain"] .stDownloadButton button:hover {
        background: #000000 !important;
        border-color: rgba(255,255,255,.32) !important;
      }
      .stApp, [data-testid="stAppViewContainer"] {
        background-color: transparent !important;
        background-image: var(--mc-background-veil),
          url("app/static/monte-carlo.png") !important;
        background-position: center !important;
        background-size: cover !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        color: var(--text-color, #31333f);
      }
      [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        background: transparent !important;
      }
      [data-testid="stHeader"], [data-testid="stSidebar"] {
        background: var(--mc-chrome) !important;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
      }
      [data-testid="stSidebar"] {
        border-right: 1px solid var(--mc-border);
      }
      [data-testid="stSidebar"] > div:first-child,
      [data-testid="stSidebarContent"],
      [data-testid="stSidebarUserContent"] {
        background: transparent !important;
      }
      [data-testid="stSidebar"] * { color: var(--text-color); }
      [data-testid="stSidebar"] .stButton button {
        background: #ffd8bd;
        border-color: #e99a66;
        font-weight: 700;
      }
      [data-testid="stSidebar"] .stButton button,
      [data-testid="stSidebar"] .stButton button * { color: #50230b !important; }
      [data-testid="stSidebar"] .stButton button:hover {
        background: #ffc79f;
        border-color: #dc7d40;
      }
      [data-testid="stSidebar"] .stDownloadButton button {
        background: #d8f3df;
        border-color: #79bc8a;
        font-weight: 700;
      }
      [data-testid="stSidebar"] .stDownloadButton button,
      [data-testid="stSidebar"] .stDownloadButton button * { color: #123d20 !important; }
      [data-testid="stSidebar"] .stDownloadButton button:hover {
        background: #c4ebce;
        border-color: #58a96e;
      }
      .hero {
        border-top: 7px solid var(--primary-color); border-bottom: 1px solid var(--mc-border);
        padding: 1.1rem 0 1.25rem; margin-bottom: 1rem;
      }
      .hero small {
        color: #e97832; font-weight: 800; letter-spacing: .15em;
        text-transform: uppercase;
      }
      .hero h1 {
        max-width: 920px; margin: .35rem 0; color: var(--text-color);
        font-size: clamp(1.9rem,4vw,3.8rem); line-height: .96; letter-spacing: -.055em;
      }
      .hero p { max-width: 760px; margin: 0; color: var(--mc-muted); }
      h1, h2, h3, label, p, li,
      [data-testid="stMarkdownContainer"],
      [data-testid="stWidgetLabel"] { color: var(--text-color); }
      [data-testid="stCaptionContainer"], [data-testid="stMetricLabel"],
      [data-testid="stMetricDelta"] { color: var(--mc-muted); }
      [data-baseweb="input"] > div, [data-baseweb="select"] > div,
      [data-testid="stFileUploaderDropzone"], [data-testid="stDataFrame"],
      [data-testid="stAlert"], [data-testid="stExpander"],
      [data-testid="stPlotlyChart"] {
        background: var(--mc-surface);
        border: 1px solid var(--mc-border) !important;
        border-radius: .5rem;
      }
      [data-testid="stPlotlyChart"] {
        border-radius: 1rem;
        overflow: hidden;
        clip-path: inset(0 round 1rem);
      }
      [data-testid="stPlotlyChart"] .js-plotly-plot,
      [data-testid="stPlotlyChart"] .plot-container,
      [data-testid="stPlotlyChart"] .svg-container {
        border-radius: inherit;
      }
      .stButton button, .stDownloadButton button {
        border: 1px solid var(--mc-border);
      }
      [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--mc-border);
      }
      [data-baseweb="tab"] { color: var(--mc-muted); }
      [data-baseweb="tab"][aria-selected="true"] {
        color: var(--text-color); border-bottom-color: var(--primary-color);
      }
      div[data-testid="stMetric"] {
        background: var(--mc-surface); border: 1px solid var(--mc-border);
        border-radius: .45rem; padding: .7rem .85rem;
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        min-width: 0;
        overflow: visible;
      }
      [data-testid="stMetricValue"],
      [data-testid="stMetricValue"] > div {
        max-width: none !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: nowrap !important;
      }
      [data-testid="stMetricValue"] {
        font-size: clamp(1.15rem, 1.8vw, 1.75rem) !important;
        letter-spacing: -.025em;
      }
      .note {
        border-left: 4px solid var(--primary-color); padding: .2rem 0 .2rem .85rem;
        color: var(--mc-muted);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.html(
    """
    <script>
      (() => {
        if (window.__mcThemeSync) window.__mcThemeSync.dispose();

        const channel = value => {
          const parts = value.match(/[0-9.]+/g);
          if (!parts || parts.length < 3) return null;
          return parts.slice(0, 3).map(Number);
        };
        const luminance = rgb => {
          const linear = rgb.map(value => {
            const normalized = value / 255;
            return normalized <= .04045
              ? normalized / 12.92
              : Math.pow((normalized + .055) / 1.055, 2.4);
          });
          return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2];
        };
        const sync = () => {
          const rgb = channel(getComputedStyle(document.body).color);
          if (!rgb) return;
          const theme = luminance(rgb) > .5 ? "dark" : "light";
          if (document.documentElement.dataset.mcTheme !== theme) {
            document.documentElement.dataset.mcTheme = theme;
          }
        };
        const observer = new MutationObserver(() => requestAnimationFrame(sync));
        observer.observe(document.body, { attributes: true, childList: true, subtree: true });
        const interval = window.setInterval(sync, 500);
        window.__mcThemeSync = {
          dispose: () => {
            observer.disconnect();
            window.clearInterval(interval);
          }
        };
        sync();
      })();
    </script>
    """,
    unsafe_allow_javascript=True,
)

def _format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f} M {unit}"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f} k {unit}"
    return f"{value:,.2f} {unit}"


def _read_csv(path: Path | None) -> pd.DataFrame | None:
    if path is None or not path.exists():
        return None
    return pd.read_csv(path)


def _zip_artifacts(artifacts: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(artifacts.items()):
            archive.writestr(name, content)
    return buffer.getvalue()


@st.cache_data(show_spinner=False)
def _run_workbook(
    file_bytes: bytes,
    file_name: str,
    simulations: int,
    seed: int,
    confidence_pct: int,
) -> dict[str, Any]:
    safe_name = Path(file_name).name or "risk_register.xlsx"
    if not safe_name.lower().endswith(".xlsx"):
        safe_name = f"{safe_name}.xlsx"

    with tempfile.TemporaryDirectory(prefix="monte-carlo-ui-") as temp_dir:
        root = Path(temp_dir)
        input_path = root / safe_name
        output_dir = root / "output"
        input_path.write_bytes(file_bytes)

        run = run_simulation_from_excel(
            input_path,
            config=SimulationConfig(
                number_of_simulations=simulations,
                random_seed=seed,
                confidence_levels=build_confidence_levels(confidence_pct),
            ),
            output_dir=output_dir,
            convergence_confidence_level=confidence_pct / 100.0,
        )

        artifacts = {
            path.name: path.read_bytes()
            for path in run.artifact_paths
            if path.exists() and path.is_file()
        }
        return {
            "metadata": {
                "project_name": run.metadata.project_name,
                "analysis_type": run.metadata.analysis_type,
                "unit": run.metadata.default_unit,
                "baseline": run.metadata.baseline_estimate,
                "schema_version": run.metadata.schema_version,
            },
            "samples": np.asarray(run.result.samples, dtype=float),
            "tables": {
                "percentiles": _read_csv(run.percentile_table_path),
                "convergence": _read_csv(run.convergence_path),
                "correlation": _read_csv(run.correlation_diagnostics_path),
                "sensitivity": _read_csv(run.sensitivity_path),
                "baseline": _read_csv(run.baseline_comparison_path),
            },
            "artifacts": artifacts,
            "simulations": simulations,
            "seed": seed,
            "confidence_pct": confidence_pct,
            "input_hash": hashlib.sha256(file_bytes).hexdigest(),
            "file_name": safe_name,
        }


def _histogram(
    samples: np.ndarray,
    baseline: float | None,
    unit: str,
    level: float,
) -> go.Figure:
    figure = go.Figure(go.Histogram(x=samples, nbinsx=70, name="Tirages"))
    for marker_level in sorted({0.50, 0.80, 0.90, level}):
        figure.add_vline(
            x=float(np.quantile(samples, marker_level)),
            line_dash="solid" if marker_level == level else "dash",
            annotation_text=f"P{marker_level * 100:g}",
        )
    if baseline is not None:
        figure.add_vline(x=baseline, line_dash="dot", annotation_text="Baseline")
    figure.update_layout(
        title="Distribution simulée",
        xaxis_title=f"Total ({unit})",
        yaxis_title="Fréquence",
        bargap=0.02,
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return figure


def _s_curve(
    samples: np.ndarray,
    baseline: float | None,
    unit: str,
    level: float,
) -> go.Figure:
    ordered = np.sort(samples)
    cumulative = np.arange(1, ordered.size + 1, dtype=float) / ordered.size
    value = float(np.quantile(samples, level))
    figure = go.Figure(go.Scatter(x=ordered, y=cumulative, mode="lines"))
    figure.add_hline(y=level, line_dash="dash")
    figure.add_vline(x=value, line_dash="dash", annotation_text=f"P{level * 100:g}")
    if baseline is not None:
        figure.add_vline(x=baseline, line_dash="dot", annotation_text="Baseline")
    figure.update_layout(
        title="Courbe cumulative (S-curve)",
        xaxis_title=f"Total ({unit})",
        yaxis_title="Probabilité de ne pas dépasser",
        yaxis_tickformat=".0%",
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return figure


def _sensitivity_chart(frame: pd.DataFrame) -> go.Figure | None:
    defined = frame.copy()
    if "is_defined" in defined:
        defined = defined.loc[defined["is_defined"].astype(str).str.lower().eq("true")]
    defined = defined.dropna(subset=["spearman_rho"]).sort_values("absolute_rho")
    if defined.empty:
        return None

    figure = go.Figure(
        go.Bar(
            x=defined["spearman_rho"],
            y=defined["item_name"],
            orientation="h",
            customdata=defined[["absolute_rho", "rank"]].to_numpy(),
            hovertemplate=(
                "%{y}<br>Spearman ρ: %{x:.3f}<br>|ρ|: %{customdata[0]:.3f}"
                "<br>Rang: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    figure.add_vline(x=0)
    figure.update_layout(
        title="Tornado de sensibilité · Spearman",
        xaxis_title="Corrélation de rang avec le total",
        yaxis_title=None,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return figure


def _convergence_chart(frame: pd.DataFrame, unit: str) -> go.Figure:
    figure = go.Figure(
        go.Scatter(
            x=frame["draw_count"],
            y=frame["estimate"],
            mode="lines+markers",
        )
    )
    recommended = frame.loc[frame["stop_recommended"].astype(str).str.lower().eq("true")]
    if not recommended.empty:
        figure.add_vline(
            x=float(recommended.iloc[0]["draw_count"]),
            line_dash="dash",
            annotation_text="stabilité détectée",
        )
    target = frame["target_percentile"].iloc[-1]
    figure.update_layout(
        title=f"Convergence de {target}",
        xaxis_title="Nombre de tirages cumulés",
        yaxis_title=f"Estimation ({unit})",
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return figure


st.markdown(
    """
    <div class="hero">
      <small>Project risk · Monte Carlo</small>
      <h1>Remplacer la marge arbitraire par une distribution défendable.</h1>
      <p>
        Chargez un registre Excel, lancez les tirages, puis lisez la réserve,
        la probabilité de dépassement et les hypothèses qui dominent le risque.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Paramètres")
    uploaded = st.file_uploader("Registre de risques (.xlsx)", type=["xlsx"])
    simulations = int(
        st.number_input(
            "Nombre de tirages",
            min_value=1_000,
            max_value=1_000_000,
            value=10_000,
            step=1_000,
        )
    )
    seed = int(st.number_input("Graîne (seed)", min_value=0, value=42, step=1))
    confidence_pct = int(
        st.select_slider(
            "Niveau de décision",
            options=[50, 80, 90, 95],
            value=90,
            format_func=lambda value: f"P{value}",
        )
    )
    run_clicked = st.button(
        "Lancer la simulation",
        type="primary",
        use_container_width=True,
        disabled=uploaded is None,
    )

    if TEMPLATE_PATH.exists():
        st.download_button(
            "Télécharger le modèle Excel",
            data=TEMPLATE_PATH.read_bytes(),
            file_name=TEMPLATE_PATH.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    st.caption("Utiliser uniquement des données autorisées et anonymisées.")

if run_clicked and uploaded is not None:
    st.session_state.pop("simulation_payload", None)
    try:
        with st.spinner("Simulation et contrôles numériques en cours…"):
            st.session_state["simulation_payload"] = _run_workbook(
                uploaded.getvalue(),
                uploaded.name,
                simulations,
                seed,
                confidence_pct,
            )
    except RiskRegisterValidationError as exc:
        st.error(f"Le registre contient {len(exc.issues)} erreur(s) de validation.")
        issues = pd.DataFrame(
            [
                {
                    "feuille": issue.sheet,
                    "ligne": issue.row,
                    "poste": issue.item_name,
                    "champ": issue.field,
                    "valeur": issue.value,
                    "message": issue.message,
                }
                for issue in exc.issues
            ]
        )
        st.dataframe(issues, use_container_width=True, hide_index=True)
    except ValidationError as exc:
        st.error(str(exc))
    except Exception as exc:  # pragma: no cover - defensive UI boundary
        st.exception(exc)

payload = st.session_state.get("simulation_payload")
if payload is None:
    st.info(
        "Chargez le modèle Excel ou un registre compatible avec le schéma 1.0. "
        "La baseline sert de référence et n'est jamais ajoutée au total simulé."
    )
    st.stop()

if uploaded is not None:
    current_hash = hashlib.sha256(uploaded.getvalue()).hexdigest()
    controls_changed = (
        current_hash != payload["input_hash"]
        or simulations != payload["simulations"]
        or seed != payload["seed"]
        or confidence_pct != payload["confidence_pct"]
    )
    if controls_changed:
        st.warning("Les paramètres ont changé depuis le dernier run. Relancez la simulation.")

metadata = payload["metadata"]
samples = payload["samples"]
tables = payload["tables"]
artifacts = payload["artifacts"]
unit = str(metadata["unit"])
baseline = metadata["baseline"]
selected_level = payload["confidence_pct"] / 100.0
snapshot = build_decision_snapshot(samples, selected_level, baseline)

with st.container(key="run-metadata"):
    st.caption(
        f"{metadata['project_name']} · {metadata['analysis_type']} · {unit} · "
        f"{payload['simulations']:,} tirages · seed {payload['seed']} · "
        f"schéma {metadata['schema_version']}"
    )

columns = st.columns([1.15, 1, 1, 1])
columns[0].metric(
    f"{snapshot.percentile_label} · niveau de décision",
    _format_value(snapshot.percentile_value, unit),
)
columns[1].metric("Moyenne simulée", _format_value(snapshot.mean, unit))
columns[2].metric(
    "P(dépassement baseline)",
    "—" if snapshot.exceedance_probability is None else f"{snapshot.exceedance_probability:.1%}",
)
columns[3].metric(
    f"Réserve jusqu'à {snapshot.percentile_label}",
    _format_value(snapshot.reserve, unit),
)

if baseline is None:
    st.info(
        "Aucune baseline n'est renseignée : la probabilité de dépassement et la réserve "
        "ne peuvent pas être calculées."
    )

decision_tab, sensitivity_tab, convergence_tab, exports_tab, method_tab = st.tabs(
    ["Décision", "Sensibilité", "Convergence", "Exports", "Méthode"]
)

with decision_tab:
    st.markdown(
        '<div class="note">Le niveau P choisi est un quantile de la distribution, '
        "pas une marge ajoutée.</div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.25, 1])
    with left:
        st.plotly_chart(
            _histogram(samples, baseline, unit, selected_level),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            _s_curve(samples, baseline, unit, selected_level),
            use_container_width=True,
        )

    percentiles = tables.get("percentiles")
    if percentiles is not None:
        st.subheader("Table de décision")
        st.dataframe(percentiles, use_container_width=True, hide_index=True)

    baseline_table = tables.get("baseline")
    if baseline_table is not None:
        st.subheader("Comparaison à la baseline")
        st.dataframe(baseline_table, use_container_width=True, hide_index=True)

with sensitivity_tab:
    sensitivity = tables.get("sensitivity")
    if sensitivity is None or sensitivity.empty:
        st.warning("Aucun résultat de sensibilité n'a été produit.")
    else:
        chart = _sensitivity_chart(sensitivity)
        if chart is None:
            st.info("Tous les postes sont déterministes : Spearman est indéfini.")
        else:
            st.plotly_chart(chart, use_container_width=True)
        st.caption(
            "Spearman mesure une association monotone. Avec des entrées corrélées, "
            "ce classement n'est ni causal ni une décomposition de variance."
        )
        st.dataframe(sensitivity, use_container_width=True, hide_index=True)

with convergence_tab:
    convergence = tables.get("convergence")
    if convergence is None or convergence.empty:
        st.warning("Aucun diagnostic de convergence n'a été produit.")
    else:
        st.plotly_chart(_convergence_chart(convergence, unit), use_container_width=True)
        recommended = convergence.loc[
            convergence["stop_recommended"].astype(str).str.lower().eq("true")
        ]
        if recommended.empty:
            st.info("Aucun point d'arrêt stable n'a été détecté dans ce run.")
        else:
            draw_count = int(recommended.iloc[0]["draw_count"])
            st.success(f"Stabilité détectée à partir d'environ {draw_count:,} tirages.")
        st.dataframe(convergence, use_container_width=True, hide_index=True)

    correlation = tables.get("correlation")
    if correlation is not None and not correlation.empty:
        st.subheader("Santé de la matrice de corrélation")
        st.dataframe(correlation, use_container_width=True, hide_index=True)

with exports_tab:
    st.download_button(
        "Télécharger tous les artefacts (.zip)",
        data=_zip_artifacts(artifacts),
        file_name="monte_carlo_results.zip",
        mime="application/zip",
        use_container_width=True,
    )
    for name, content in sorted(artifacts.items()):
        suffix = Path(name).suffix.lower()
        mime = {".csv": "text/csv", ".png": "image/png"}.get(
            suffix,
            "application/octet-stream",
        )
        st.download_button(
            name,
            data=content,
            file_name=name,
            mime=mime,
            key=f"download-{name}",
        )

with method_tab:
    with st.container(key="method-content"):
        st.markdown(
            """
            **P50 / P80 / P90 / P95** — valeur non dépassée dans environ 50 %, 80 %, 90 % ou
            95 % des tirages du modèle.

            **Probabilité de dépassement** — fréquence stricte où le total simulé est supérieur
            à la baseline du classeur.

            **Réserve** — `max(Px - baseline, 0)`. La baseline reste une référence externe.

            **Tornado Spearman** — outil de priorisation des postes associés aux variations du
            total, pas preuve de causalité.

            **Convergence** — stabilité cumulative du percentile sélectionné. Elle renseigne sur
            le nombre de tirages, pas sur la qualité des hypothèses métier.
            """
        )
