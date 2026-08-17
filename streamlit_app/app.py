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

from monte_carlo_simulator.application.hypotheses import load_editable_risk_register
from monte_carlo_simulator.application.presentation import (
    build_confidence_levels,
    build_decision_snapshot,
)
from monte_carlo_simulator.application.service import run_simulation_from_excel
from monte_carlo_simulator.exceptions import RiskRegisterValidationError, ValidationError
from monte_carlo_simulator.io import create_risk_register_workbook, load_risk_register
from monte_carlo_simulator.models import SimulationConfig

APP_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = APP_ROOT / "data" / "templates" / "risk_register_template.xlsx"
NAVIGATION_ITEMS = ("Configuration des hypothèses", "Paramètres", "Simulation")
RISK_COLUMNS = (
    "name",
    "distribution",
    "minimum",
    "most_likely",
    "maximum",
    "mean",
    "standard_deviation",
    "probability",
    "impact",
    "lambda_shape",
    "category",
    "unit",
    "enabled",
    "notes",
)

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
          rgba(220,231,224,.76), rgba(194,213,204,.80)
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
        --mc-surface: rgba(22,44,32,.80);
        --mc-border: rgba(93,202,165,.16);
        --mc-muted: rgba(255,255,255,.82);
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
      :root[data-mc-theme="dark"] [data-testid="stHeader"] .mc-engine-title {
        color: #e97832 !important;
      }
      :root[data-mc-theme="dark"] .section-heading h1 {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] div[data-testid="stMetric"] {
        background: #0e1117 !important;
        border-color: var(--mc-border) !important;
      }
      :root[data-mc-theme="dark"] div[data-testid="stMetric"],
      :root[data-mc-theme="dark"] div[data-testid="stMetric"] * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-testid="stMarkdownContainer"],
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-testid="stMarkdownContainer"] *,
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-testid="stWidgetLabel"],
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-testid="stWidgetLabel"] *,
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-testid="stCaptionContainer"],
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-testid="stCaptionContainer"] *,
      :root[data-mc-theme="dark"] [data-testid="stMain"] [data-baseweb="tab"] {
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
        background: #0e1117 !important;
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
          url("/app/static/monte-carlo.png") !important;
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
      .sidebar-company-logo {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        padding: .25rem 0 .65rem;
      }
      .sidebar-company-logo img {
        display: block;
        width: 105px;
        height: auto;
        margin: 0 auto;
      }
      [data-testid="stSidebar"] * { color: var(--text-color); }
      [data-testid="stSidebar"] .stButton button {
        background: transparent;
        border: 1px solid transparent;
        border-left: 3px solid transparent;
        border-radius: .625rem;
        font-weight: 500;
        justify-content: flex-start;
        text-align: left;
        min-height: 2.8rem;
        padding-left: .75rem;
      }
      [data-testid="stSidebar"] .stButton button p {
        width: 100%;
        text-align: left;
      }
      [data-testid="stSidebar"] .stButton button > div,
      [data-testid="stSidebar"] .stButton button > span {
        width: 100%;
        justify-content: flex-start !important;
        text-align: left !important;
      }
      [data-testid="stSidebar"] .stButton button,
      [data-testid="stSidebar"] .stButton button * {
        color: var(--mc-muted) !important;
      }
      [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(13,124,102,.08);
        border-color: rgba(13,124,102,.10);
      }
      [data-testid="stSidebar"] .stButton button:hover,
      [data-testid="stSidebar"] .stButton button:hover * {
        color: #0d7c66 !important;
      }
      [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: rgba(13,124,102,.11);
        border-color: rgba(13,124,102,.10);
        border-left-color: #0d7c66;
        box-shadow: none;
        font-weight: 600;
      }
      [data-testid="stSidebar"] .stButton button[kind="primary"],
      [data-testid="stSidebar"] .stButton button[kind="primary"] * {
        color: #0d7c66 !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(93,202,165,.07);
        border-color: rgba(93,202,165,.08);
      }
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] .stButton button:hover,
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] .stButton button:hover *,
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] .stButton button[kind="primary"],
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] .stButton button[kind="primary"] * {
        color: #5dcaa5 !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: rgba(93,202,165,.10);
        border-color: rgba(93,202,165,.12);
        border-left-color: #5dcaa5;
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
      [data-testid="stSidebarCollapseButton"] button svg,
      [data-testid="stExpandSidebarButton"] svg {
        display: none !important;
      }
      [data-testid="stSidebarCollapseButton"] button > *,
      [data-testid="stExpandSidebarButton"] > * {
        display: none !important;
      }
      [data-testid="stSidebarCollapseButton"] button::before,
      [data-testid="stExpandSidebarButton"]::before {
        content: "";
        display: block;
        width: 19px;
        height: 14px;
        background: linear-gradient(
          to bottom,
          currentColor 0 2px,
          transparent 2px 6px,
          currentColor 6px 8px,
          transparent 8px 12px,
          currentColor 12px 14px
        );
        border-radius: 1px;
      }
      .mc-engine-title {
        display: none;
        align-items: center;
        margin-left: .7rem;
        color: #e97832;
        font: 750 1.15rem/1.2 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        letter-spacing: -.015em;
        white-space: nowrap;
      }
      .mc-engine-title[data-mounted="true"] { display: flex; }
      .mc-engine-title[data-placement="open"] {
        position: absolute;
        top: 50%;
        left: 1rem;
        z-index: 1;
        margin-left: 0;
        transform: translateY(-50%);
        pointer-events: none;
      }
      .section-heading { margin-bottom: 1.25rem; }
      .section-heading h1 { margin-bottom: .35rem; }
      .section-heading p { max-width: 780px; color: var(--mc-muted); }
      .st-key-hypothesis-metadata,
      .st-key-hypothesis-table,
      .st-key-parameter-panel {
        background: var(--mc-surface); border: 1px solid var(--mc-border);
        border-radius: .8rem; padding: 1rem 1.15rem 1.15rem;
        backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
      }
      .st-key-parameter-panel {
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 0;
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
      }
      .parameter-field-title {
        margin: 1rem 0 .4rem;
        color: var(--text-color);
        font-size: 1.08rem;
        line-height: 1.35;
        font-weight: 750;
      }
      .simulation-theme-marker { display: none; }
      .st-key-parameter-upload-card,
      .st-key-parameter-simulations-card,
      .st-key-parameter-seed-card {
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 0;
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
      }
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] {
        background: #cfd4d8 !important;
        border-color: rgba(14,17,23,.22) !important;
      }
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] *,
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] button,
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] button * {
        color: #0e1117 !important;
      }
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] button {
        background: #eef0f2 !important;
        border-color: rgba(14,17,23,.22) !important;
      }
      .st-key-parameter-simulations-card [data-baseweb="input"] > div,
      .st-key-parameter-seed-card [data-baseweb="input"] > div {
        background: #cfd4d8 !important;
        border-color: rgba(14,17,23,.22) !important;
        color: #0e1117 !important;
      }
      .st-key-parameter-simulations-card [data-baseweb="input"] *,
      .st-key-parameter-seed-card [data-baseweb="input"] * {
        color: #0e1117 !important;
      }
      :root[data-mc-theme="light"]
      .st-key-parameter-simulations-card [data-baseweb="input"] > div,
      :root[data-mc-theme="light"]
      .st-key-parameter-seed-card [data-baseweb="input"] > div {
        background: #cfd4d8 !important;
        border-color: rgba(14,17,23,.22) !important;
      }
      :root[data-mc-theme="dark"]
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] {
        background: #0e1117 !important;
        border-color: rgba(255,255,255,.18) !important;
      }
      :root[data-mc-theme="dark"]
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] *,
      :root[data-mc-theme="dark"]
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] button * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"]
      .st-key-parameter-upload-card [data-testid="stFileUploaderDropzone"] button {
        background: #252a32 !important;
        border-color: rgba(255,255,255,.20) !important;
      }
      :root[data-mc-theme="dark"]
      .st-key-parameter-simulations-card [data-baseweb="input"] > div,
      :root[data-mc-theme="dark"]
      .st-key-parameter-seed-card [data-baseweb="input"] > div {
        background: #0e1117 !important;
        border-color: rgba(255,255,255,.18) !important;
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"]
      .st-key-parameter-simulations-card [data-baseweb="input"] *,
      :root[data-mc-theme="dark"]
      .st-key-parameter-seed-card [data-baseweb="input"] * {
        color: #ffffff !important;
      }
      :root[data-mc-theme="dark"] .st-key-exports-content .stDownloadButton button {
        background: #0e1117 !important;
        border-color: rgba(255,255,255,.16) !important;
      }
      .st-key-parameter-panel [data-testid="stWidgetLabel"] p {
        font-size: 1.08rem !important;
        line-height: 1.35 !important;
        font-weight: 750 !important;
      }
      .st-key-run-simulation button {
        background: #ffd8bd !important;
        border-color: #e99a66 !important;
      }
      .st-key-run-simulation button,
      .st-key-run-simulation button * {
        color: #50230b !important;
        font-weight: 750 !important;
      }
      .st-key-download-template button {
        background: #d8f3df !important;
        border-color: #79bc8a !important;
      }
      .st-key-download-template button,
      .st-key-download-template button * {
        color: #123d20 !important;
        font-weight: 750 !important;
      }
      :root[data-mc-theme="dark"] .st-key-run-simulation button {
        background: #d9854d !important;
        border-color: #bd6e3d !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stMain"]
      .st-key-download-template button {
        background: #9bc9a7 !important;
        border-color: #74a982 !important;
      }
      :root[data-mc-theme="dark"] [data-testid="stMain"]
      .st-key-download-template button,
      :root[data-mc-theme="dark"] [data-testid="stMain"]
      .st-key-download-template button * {
        color: #123d20 !important;
      }
      :root[data-mc-theme="light"]:has(.simulation-theme-marker)
      [data-testid="stMain"] div[data-testid="stMetric"],
      :root[data-mc-theme="light"]:has(.simulation-theme-marker)
      [data-testid="stMain"] [data-testid="stPlotlyChart"],
      :root[data-mc-theme="light"]:has(.simulation-theme-marker)
      [data-testid="stMain"] [data-testid="stDataFrame"],
      :root[data-mc-theme="light"]:has(.simulation-theme-marker)
      [data-testid="stMain"] [data-testid="stAlert"],
      :root[data-mc-theme="light"]:has(.simulation-theme-marker)
      [data-testid="stMain"] [data-testid="stExpander"],
      :root[data-mc-theme="light"]:has(.simulation-theme-marker)
      [data-testid="stMain"] .stDownloadButton button {
        background: #cfd4d8 !important;
        border-color: rgba(14,17,23,.18) !important;
      }
      .mc-theme-switcher {
        display: flex;
        align-items: center;
        gap: .2rem;
        margin-left: .35rem;
        padding: .18rem;
        border: 1px solid var(--mc-border);
        border-radius: .55rem;
        background: var(--mc-chrome);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
      }
      .mc-theme-switcher:not([data-mounted="true"]) {
        display: none;
      }
      .mc-theme-switcher button {
        min-height: 1.9rem;
        padding: .25rem .5rem;
        border: 0;
        border-radius: .4rem;
        background: transparent;
        color: var(--text-color);
        cursor: pointer;
        font: 600 .75rem/1 system-ui, sans-serif;
      }
      .mc-theme-switcher button:hover {
        background: rgba(13,124,102,.12);
      }
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

st.html(
    """
    <div class="mc-theme-switcher" id="mc-theme-switcher" aria-label="Thème de l'interface">
      <button type="button" data-theme-choice="light" title="Mode clair">Clair</button>
      <button type="button" data-theme-choice="dark" title="Mode sombre">Sombre</button>
      <button type="button" data-theme-choice="system" title="Thème du système">Système</button>
    </div>
    <div class="mc-engine-title" id="mc-engine-title">Moteur Monte-Carlo</div>
    <script>
      (() => {
        const switcher = document.getElementById("mc-theme-switcher");
        const engineTitle = document.getElementById("mc-engine-title");
        if (!switcher || switcher.dataset.ready === "true") return;
        switcher.dataset.ready = "true";

        const placeSwitcher = () => {
          const deploy = document.querySelector('[data-testid="stAppDeployButton"]');
          if (deploy && deploy.nextElementSibling !== switcher) {
            deploy.insertAdjacentElement("afterend", switcher);
          }
          if (deploy) switcher.dataset.mounted = "true";

          const expandButton = document.querySelector(
            '[data-testid="stExpandSidebarButton"]'
          );
          const toolbar = document.querySelector('[data-testid="stToolbar"]');
          if (engineTitle && expandButton && expandButton.nextElementSibling !== engineTitle) {
            expandButton.insertAdjacentElement("afterend", engineTitle);
          } else if (
            engineTitle && !expandButton && toolbar && toolbar.firstElementChild !== engineTitle
          ) {
            toolbar.insertAdjacentElement("afterbegin", engineTitle);
          }
          if (engineTitle) {
            engineTitle.dataset.mounted = expandButton || toolbar ? "true" : "false";
            engineTitle.dataset.placement = expandButton ? "closed" : "open";
          }
        };

        const chooseNativeTheme = choice => {
          const menuButton = document.querySelector('[data-testid="stMainMenuButton"]');
          if (!menuButton) return;
          if (!document.querySelector('[data-testid="stThemeSwitcher"]')) menuButton.click();
          window.setTimeout(() => {
            const aliases = {
              light: ["light", "clair"],
              dark: ["dark", "sombre"],
              system: ["system"]
            };
            const options = document.querySelectorAll(
              '[data-testid="stThemeSwitcher"] [role="menuitemradio"], ' +
              '[data-testid="stThemeSwitcher"] [role="radio"], ' +
              '[data-testid="stThemeSwitcher"] button'
            );
            const target = Array.from(options).find(option => {
              const text = (option.textContent || "").trim().toLowerCase();
              return aliases[choice].some(alias => text.includes(alias));
            });
            if (target) target.click();
          }, 80);
        };

        switcher.addEventListener("click", event => {
          const button = event.target.closest("button[data-theme-choice]");
          if (button) chooseNativeTheme(button.dataset.themeChoice);
        });
        const observer = new MutationObserver(placeSwitcher);
        observer.observe(document.body, { childList: true, subtree: true });
        window.setInterval(placeSwitcher, 600);
        placeSwitcher();
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
    counts, edges = np.histogram(samples, bins=70)
    centers = (edges[:-1] + edges[1:]) / 2
    intervals = np.column_stack((edges[:-1], edges[1:]))
    figure = go.Figure(
        go.Bar(
            x=centers,
            y=counts,
            width=np.diff(edges),
            customdata=intervals,
            hovertemplate=(
                "Intervalle : %{customdata[0]:,.2f} – %{customdata[1]:,.2f}<br>"
                "Simulations : %{y:,}<extra></extra>"
            ),
            name="Tirages",
        )
    )
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
    # Keep the browser fluid for very large runs while retaining both endpoints.
    indices = np.unique(np.linspace(0, ordered.size - 1, min(5_000, ordered.size), dtype=int))
    value = float(np.quantile(samples, level))
    figure = go.Figure(
        go.Scatter(
            x=ordered[indices],
            y=cumulative[indices],
            mode="lines",
            hovertemplate="Coût : %{x:,.2f}<br>Probabilité cumulée : %{y:.2%}<extra></extra>",
        )
    )
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


def _section_heading(title: str, description: str) -> None:
    st.markdown(
        f'<div class="section-heading"><h1>{title}</h1><p>{description}</p></div>',
        unsafe_allow_html=True,
    )


def _navigate(section: str) -> None:
    st.session_state["active_section"] = section


def _default_hypotheses() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": "Études et conception",
                "distribution": "triangular",
                "minimum": 100_000.0,
                "most_likely": 140_000.0,
                "maximum": 220_000.0,
                "category": "Ingénierie",
                "unit": "",
                "enabled": True,
                "notes": "Estimation à trois points.",
            },
            {
                "name": "Retard administratif",
                "distribution": "event",
                "probability": 0.20,
                "impact": 80_000.0,
                "category": "Planning",
                "unit": "",
                "enabled": True,
                "notes": "Probabilité × impact.",
            },
        ],
        columns=RISK_COLUMNS,
    )


def _clean_cell(value: object) -> object:
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _create_configured_workbook(
    project_name: str,
    analysis_type: str,
    default_unit: str,
    baseline_estimate: float | None,
    description: str,
    hypotheses: pd.DataFrame,
) -> tuple[bytes, str]:
    rows = []
    for raw_row in hypotheses.to_dict(orient="records"):
        cleaned = {column: _clean_cell(raw_row.get(column)) for column in RISK_COLUMNS}
        if cleaned["name"] is None:
            continue
        if cleaned["enabled"] is None:
            cleaned["enabled"] = True
        rows.append(cleaned)
    if not rows:
        raise ValidationError("Ajoutez au moins un poste de risque nommé.")

    safe_stem = "".join(
        character if character.isalnum() else "_" for character in project_name.strip()
    ).strip("_")
    file_name = f"{safe_stem or 'registre_risques'}_monte_carlo.xlsx"
    with tempfile.TemporaryDirectory(prefix="monte-carlo-register-") as temp_dir:
        output_path = Path(temp_dir) / file_name
        create_risk_register_workbook(
            output_path,
            metadata_values={
                "project_name": project_name,
                "analysis_type": analysis_type,
                "default_unit": default_unit,
                "baseline_estimate": baseline_estimate,
                "description": description or None,
            },
            risk_rows=rows,
        )
        load_risk_register(output_path)
        return output_path.read_bytes(), file_name


def _load_editable_workbook(file_bytes: bytes, file_name: str) -> tuple[Any, pd.DataFrame]:
    """Load uploaded Excel bytes through the validated application adapter."""
    safe_name = Path(file_name).name or "risk_register.xlsx"
    with tempfile.TemporaryDirectory(prefix="monte-carlo-import-") as temp_dir:
        path = Path(temp_dir) / safe_name
        path.write_bytes(file_bytes)
        editable = load_editable_risk_register(path)
    rows = editable.rows.reindex(columns=RISK_COLUMNS)
    return editable.metadata, rows


def _display_validation_error(exc: RiskRegisterValidationError) -> None:
    st.error(f"Le registre contient {len(exc.issues)} erreur(s) de validation.")
    st.dataframe(
        pd.DataFrame(
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
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-company-logo">'
            '<img src="/app/static/logo-choubel.png" alt="Choubel Consulting">'
            "</div>",
            unsafe_allow_html=True,
        )
        for label, icon in zip(NAVIGATION_ITEMS, ("⚙️", "🎛️", "📊"), strict=True):
            st.button(
                f"{icon}  {label}",
                key=f"nav-{label}",
                type="primary" if st.session_state["active_section"] == label else "secondary",
                use_container_width=True,
                on_click=_navigate,
                args=(label,),
            )
        st.caption("Utilisez uniquement des données autorisées et anonymisées.")


def _render_hypothesis_configuration() -> None:
    _section_heading(
        "Configuration des hypothèses",
        "Définissez le projet et ses postes de risque, puis générez un registre Excel "
        "directement compatible avec la plateforme.",
    )
    uploaded = st.file_uploader(
        "Importer des hypothèses Excel pour les modifier",
        type=["xlsx"],
        key="hypothesis-import",
        help=(
            "Le fichier est validé puis converti en modèle éditable ; "
            "la simulation utilisera vos corrections."
        ),
    )
    if st.button("Charger dans l’éditeur", disabled=uploaded is None, width="stretch"):
        try:
            metadata, imported_rows = _load_editable_workbook(uploaded.getvalue(), uploaded.name)
            st.session_state.update(
                hypothesis_rows=imported_rows,
                initial_hypothesis_rows=imported_rows.copy(deep=True),
                hypothesis_editor_revision=(
                    st.session_state.get("hypothesis_editor_revision", 0) + 1
                ),
                hypothesis_project_name=metadata.project_name,
                hypothesis_analysis="Coûts" if metadata.analysis_type == "cost" else "Durées",
                hypothesis_unit=metadata.default_unit,
                hypothesis_baseline_enabled=metadata.baseline_estimate is not None,
                hypothesis_baseline=float(metadata.baseline_estimate or 0.0),
                hypothesis_description=metadata.description or "",
            )
            st.success(f"{len(imported_rows)} poste(s) importé(s) dans l’éditeur.")
            st.rerun()
        except RiskRegisterValidationError as exc:
            _display_validation_error(exc)
        except ValidationError as exc:
            st.error(str(exc))

    with st.container(key="hypothesis-metadata"):
        st.subheader("Informations du projet")
        left, middle, right = st.columns([1.45, 1, 1])
        project_name = left.text_input(
            "Nom du projet", value="Nouveau projet", key="hypothesis_project_name"
        )
        analysis_label = middle.selectbox(
            "Type d'analyse", ("Coûts", "Durées"), key="hypothesis_analysis"
        )
        default_unit = right.text_input("Unité commune", value="MAD", key="hypothesis_unit")
        baseline_enabled = st.checkbox(
            "Renseigner une baseline", value=True, key="hypothesis_baseline_enabled"
        )
        baseline_estimate = (
            float(
                st.number_input(
                    "Estimation de référence",
                    min_value=0.0,
                    value=250_000.0,
                    step=10_000.0,
                    key="hypothesis_baseline",
                )
            )
            if baseline_enabled
            else None
        )
        description = st.text_area(
            "Description",
            placeholder="Contexte non confidentiel et sources des hypothèses.",
            key="hypothesis_description",
        )

    st.write("")
    with st.container(key="hypothesis-table"):
        st.subheader("Registre des risques")
        st.caption(
            "Utilisez uniquement les paramètres de la distribution choisie. "
            "Les autres cellules peuvent rester vides."
        )
        if "hypothesis_rows" not in st.session_state:
            st.session_state["hypothesis_rows"] = _default_hypotheses()
        hypotheses = st.data_editor(
            st.session_state["hypothesis_rows"],
            key=f"hypothesis_editor_{st.session_state.get('hypothesis_editor_revision', 0)}",
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            height=430,
            column_config={
                "name": st.column_config.TextColumn("Poste", required=True, width="medium"),
                "distribution": st.column_config.SelectboxColumn(
                    "Distribution",
                    options=["triangular", "pert", "uniform", "normal", "lognormal", "event"],
                    required=True,
                    width="medium",
                ),
                "minimum": st.column_config.NumberColumn("Minimum", format="%.2f"),
                "most_likely": st.column_config.NumberColumn("Plus probable", format="%.2f"),
                "maximum": st.column_config.NumberColumn("Maximum", format="%.2f"),
                "mean": st.column_config.NumberColumn("Moyenne", format="%.2f"),
                "standard_deviation": st.column_config.NumberColumn("Écart-type", format="%.2f"),
                "probability": st.column_config.NumberColumn(
                    "Probabilité", min_value=0.0, max_value=1.0, format="%.3f"
                ),
                "impact": st.column_config.NumberColumn("Impact", format="%.2f"),
                "lambda_shape": st.column_config.NumberColumn(
                    "Lambda PERT", min_value=0.01, format="%.2f"
                ),
                "category": st.column_config.TextColumn("Catégorie"),
                "unit": st.column_config.TextColumn("Unité"),
                "enabled": st.column_config.CheckboxColumn("Actif", default=True),
                "notes": st.column_config.TextColumn("Notes", width="large"),
            },
        )
        st.session_state["hypothesis_rows"] = hypotheses

        if "initial_hypothesis_rows" not in st.session_state:
            st.session_state["initial_hypothesis_rows"] = hypotheses.copy(deep=True)
        if st.button("Réinitialiser les hypothèses", key="reset-hypotheses"):
            st.session_state["hypothesis_rows"] = st.session_state["initial_hypothesis_rows"].copy(
                deep=True
            )
            st.session_state["hypothesis_editor_revision"] = (
                st.session_state.get("hypothesis_editor_revision", 0) + 1
            )
            st.rerun()

    validate_column, use_column = st.columns(2)
    validate_clicked = validate_column.button(
        "Valider et préparer l'Excel", key="validate-hypotheses", width="stretch"
    )
    use_clicked = use_column.button(
        "Utiliser pour la simulation",
        key="use-hypotheses",
        type="primary",
        width="stretch",
    )
    if validate_clicked or use_clicked:
        try:
            workbook_bytes, file_name = _create_configured_workbook(
                project_name,
                "cost" if analysis_label == "Coûts" else "duration",
                default_unit,
                baseline_estimate,
                description,
                hypotheses,
            )
            st.session_state["configured_workbook"] = workbook_bytes
            st.session_state["configured_workbook_name"] = file_name
            st.success("Les hypothèses sont valides et le registre Excel est prêt.")
            if use_clicked:
                st.session_state["active_section"] = "Paramètres"
                st.rerun()
        except RiskRegisterValidationError as exc:
            _display_validation_error(exc)
        except ValidationError as exc:
            st.error(str(exc))

    if st.session_state.get("configured_workbook") is not None:
        st.download_button(
            "Télécharger le registre Excel compatible",
            data=st.session_state["configured_workbook"],
            file_name=st.session_state["configured_workbook_name"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download-configured-workbook",
            width="stretch",
        )


def _render_parameters() -> None:
    _section_heading(
        "Paramètres de simulation",
        "Choisissez la source, le nombre de tirages, la graine et le niveau de confiance.",
    )
    with st.container(key="parameter-panel"):
        st.markdown(
            '<div class="parameter-field-title">Importer un registre (.xlsx)</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="parameter-upload-card"):
            uploaded = st.file_uploader(
                "Importer un registre (.xlsx)",
                type=["xlsx"],
                key="simulation-upload",
                label_visibility="collapsed",
            )

        configured = st.session_state.get("configured_workbook")
        if uploaded is not None:
            source_bytes, source_name = uploaded.getvalue(), uploaded.name
            st.success(f"Source active : fichier importé « {source_name} ».")
        elif configured is not None:
            source_bytes = configured
            source_name = st.session_state["configured_workbook_name"]
            st.success(f"Source active : hypothèses configurées « {source_name} ».")
        else:
            source_bytes, source_name = None, ""
            st.info("Importez un fichier ou préparez les hypothèses dans la première section.")

        st.markdown("#### Modèle Excel")
        st.caption("Préparez aussi le registre hors ligne si nécessaire.")
        if TEMPLATE_PATH.exists():
            st.download_button(
                "Télécharger le modèle Excel",
                data=TEMPLATE_PATH.read_bytes(),
                file_name=TEMPLATE_PATH.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download-template",
                width="stretch",
            )

        st.markdown(
            '<div class="parameter-field-title">Nombre de tirages</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="parameter-simulations-card"):
            simulations = int(
                st.number_input(
                    "Nombre de tirages",
                    1_000,
                    1_000_000,
                    10_000,
                    1_000,
                    label_visibility="collapsed",
                )
            )

        st.markdown(
            '<div class="parameter-field-title">Graine aléatoire</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="parameter-seed-card"):
            seed = int(
                st.number_input(
                    "Graine aléatoire",
                    min_value=0,
                    value=42,
                    step=1,
                    label_visibility="collapsed",
                )
            )
        confidence_pct = int(
            st.select_slider(
                "Niveau de décision",
                options=[50, 80, 90, 95],
                value=90,
                format_func=lambda value: f"P{value}",
            )
        )
        st.caption("Les fichiers sont traités localement et ne sont pas conservés.")
        run_clicked = st.button(
            "Lancer la simulation",
            key="run-simulation",
            type="primary",
            width="stretch",
            disabled=source_bytes is None,
        )

    if run_clicked and source_bytes is not None:
        try:
            with st.spinner("Simulation et contrôles numériques en cours…"):
                st.session_state["simulation_payload"] = _run_workbook(
                    source_bytes, source_name, simulations, seed, confidence_pct
                )
            st.session_state["active_section"] = "Simulation"
            st.rerun()
        except RiskRegisterValidationError as exc:
            _display_validation_error(exc)
        except ValidationError as exc:
            st.error(str(exc))
        except Exception as exc:  # pragma: no cover
            st.exception(exc)


def _render_simulation() -> None:
    st.markdown('<span class="simulation-theme-marker"></span>', unsafe_allow_html=True)
    _section_heading(
        "Simulation",
        "Interprétez le niveau de confiance, la réserve, les facteurs dominants "
        "et la stabilité du dernier calcul.",
    )
    payload = st.session_state.get("simulation_payload")
    if payload is None:
        st.info(
            "Aucune simulation n'a encore été lancée. Préparez les hypothèses, "
            "puis utilisez la section Paramètres."
        )
        if st.button("Ouvrir les paramètres", type="primary"):
            st.session_state["active_section"] = "Paramètres"
            st.rerun()
        return

    metadata, samples, tables = payload["metadata"], payload["samples"], payload["tables"]
    artifacts = payload["artifacts"]
    unit, baseline = str(metadata["unit"]), metadata["baseline"]
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
        (
            "—"
            if snapshot.exceedance_probability is None
            else f"{snapshot.exceedance_probability:.1%}"
        ),
    )
    columns[3].metric(
        f"Réserve jusqu'à {snapshot.percentile_label}",
        _format_value(snapshot.reserve, unit),
    )
    if baseline is None:
        st.info("Aucune baseline n'est renseignée pour ce registre.")

    decision_tab, sensitivity_tab, convergence_tab, exports_tab, method_tab = st.tabs(
        ["Décision", "Sensibilité", "Convergence", "Exports", "Méthode"]
    )
    with decision_tab:
        st.markdown(
            '<div class="note">Le niveau P choisi est un quantile, pas une marge ajoutée.</div>',
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
        if tables.get("percentiles") is not None:
            st.subheader("Table de décision")
            st.dataframe(tables["percentiles"], use_container_width=True, hide_index=True)
        if tables.get("baseline") is not None:
            st.subheader("Comparaison à la baseline")
            st.dataframe(tables["baseline"], use_container_width=True, hide_index=True)

    with sensitivity_tab:
        sensitivity = tables.get("sensitivity")
        if sensitivity is None or sensitivity.empty:
            st.warning("Aucun résultat de sensibilité n'a été produit.")
        else:
            chart = _sensitivity_chart(sensitivity)
            if chart is not None:
                st.plotly_chart(chart, use_container_width=True)
            st.caption("Spearman mesure une association monotone, pas une causalité.")
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
                st.info("Aucun point d'arrêt stable n'a été détecté.")
            else:
                draw_count = int(recommended.iloc[0]["draw_count"])
                st.success(f"Stabilité détectée à partir d'environ {draw_count:,} tirages.")
            st.dataframe(convergence, use_container_width=True, hide_index=True)
        correlation = tables.get("correlation")
        if correlation is not None and not correlation.empty:
            st.subheader("Santé de la matrice de corrélation")
            st.dataframe(correlation, use_container_width=True, hide_index=True)

    with exports_tab:
        with st.container(key="exports-content"):
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
                    suffix, "application/octet-stream"
                )
                st.download_button(
                    name,
                    content,
                    file_name=name,
                    mime=mime,
                    key=f"download-{name}",
                )

    with method_tab:
        st.markdown(
            """
            **P50 / P80 / P90 / P95** — valeur non dépassée dans environ 50 %, 80 %,
            90 % ou 95 % des tirages.

            **Probabilité de dépassement** — fréquence stricte où le total simulé est
            supérieur à la baseline.

            **Réserve** — écart positif entre le percentile choisi et la baseline.

            **Tornado Spearman** — priorisation des postes, pas preuve de causalité.

            **Convergence** — stabilité du percentile, pas validation des hypothèses métier.
            """
        )


st.session_state.setdefault("active_section", "Configuration des hypothèses")
_render_sidebar()
active_section = st.session_state["active_section"]
if active_section == "Configuration des hypothèses":
    _render_hypothesis_configuration()
elif active_section == "Paramètres":
    _render_parameters()
else:
    _render_simulation()
