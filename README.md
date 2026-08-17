# Monte-Carlo-Simulator

Python application for probabilistic project cost and schedule risk analysis. The project turns an Excel risk register into a simulated total distribution, decision percentiles, baseline reserves, correlation diagnostics, convergence evidence and sensitivity outputs.

## Current status — S5 interface migration

The simulation engine, CLI and Streamlit workflow remain available. Week 5 adds a separated web architecture: a thin FastAPI adapter exposes the existing application service to a React/TypeScript interface designed for clearer decision reading and scenario comparison.

Available features:

- vectorized and reproducible Monte Carlo simulation with NumPy;
- six distributions: triangular, Beta-PERT, uniform, normal, arithmetic-parameterized log-normal and Bernoulli × impact event risk;
- versioned Excel schema `1.0` with aggregated validation errors;
- optional correlations through a Gaussian copula and Cholesky decomposition;
- strict matrix policy: invalid correlation matrices are rejected and never repaired silently;
- histogram and empirical S-curve;
- P50/P80/P90/P95 and configurable percentiles;
- baseline exceedance probability and non-negative percentile reserves;
- Spearman sensitivity and tornado chart;
- cumulative percentile convergence diagnostics;
- historical Streamlit workflow with downloadable artifact bundle;
- React/TypeScript decision interface with drag-and-drop upload, responsive layout and reference-vs-current scenario comparison;
- FastAPI adapter that reuses `run_simulation_from_excel` instead of duplicating probabilistic rules;
- reproducible synthetic acceptance case and consultant-validation protocol;
- user, methodology, handover and restitution documentation.

## Installation

Python 3.11+ is required. Node.js is required only for the S5 React interface.

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,ui,web]"
```

## S5 React / TypeScript interface

Start the Python API:

```bash
uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`.

The new interface provides:

1. drag-and-drop upload of a schema-1.0 `.xlsx` register;
2. simulation count, random seed and P50/P80/P90/P95 selection;
3. immediate reading of mean, P80, P90 and baseline exposure;
4. browser-rendered distribution and empirical S-curve;
5. ranked Spearman sensitivity;
6. a reference-run mechanism for comparing a base case with a modified/mitigated workbook.

For the architecture and S5 design choices, see [`docs/s5_web_interface.md`](docs/s5_web_interface.md).

### Production-style build

```bash
cd web
npm install
npm run build
cd ..
uvicorn monte_carlo_simulator.web_api:app --host 0.0.0.0 --port 8000
```

When `web/dist` exists, FastAPI serves the compiled single-page application directly.

## Streamlit interface

The S4 interface remains available as a stable fallback:

```bash
streamlit run streamlit_app/app.py
```

It lets a consultant upload a workbook, execute a simulation, inspect Plotly views and download the generated artifact bundle.

## CLI

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

Without `--input`, the historical fictitious demonstration remains available:

```bash
python -m monte_carlo_simulator.cli
```

## Excel risk register

The public fictitious template is [`data/templates/risk_register_template.xlsx`](data/templates/risk_register_template.xlsx).

Required sheets:

- `metadata` — schema version, project name, `cost`/`duration`, common unit and optional baseline;
- `risk_register` — one active cost/duration item or event risk per row;
- `instructions` — embedded schema guidance.

Optional sheet:

- `correlations` — square matrix aligned by active item names.

Supported canonical distributions and required parameters:

| Distribution | Required parameters |
| --- | --- |
| `triangular` | `minimum`, `most_likely`, `maximum` |
| `pert` | `minimum`, `most_likely`, `maximum`; optional `lambda_shape` |
| `uniform` | `minimum`, `maximum` |
| `normal` | `mean`, `standard_deviation` |
| `lognormal` | arithmetic `mean`, arithmetic `standard_deviation` |
| `event` | `probability`, `impact` |

The baseline is contextual information only. It is never added implicitly to the simulated total.

## Decision artifacts

A standard Excel run produces:

- `simulation_summary.csv`;
- `simulation_histogram.png`;
- `simulation_s_curve.png`;
- `percentile_decision_table.csv`;
- `convergence_diagnostics.csv`;
- `sensitivity_summary.csv`;
- `sensitivity_tornado.png`.

If a baseline exists, the workflow adds `baseline_comparison.csv`. If correlations are supplied, it adds `correlation_diagnostics.csv`.

## Reproducible S3/S4 validation path

Generate and execute the synthetic correlated acceptance case with:

```bash
python -m scripts.run_s3_acceptance_case
```

Outputs are written under `data/output/s3_acceptance/`. This case validates the software path and numerical invariants; it does not validate the credibility of a real client's assumptions.

For field validation, use:

- [`docs/consultant_validation_workshop.md`](docs/consultant_validation_workshop.md);
- [`data/templates/consultant_validation_log.csv`](data/templates/consultant_validation_log.csv).

## Documentation

- [S5 React/TypeScript architecture](docs/s5_web_interface.md)
- [30-minute user guide](docs/user_guide_30min.md)
- [Detailed Excel/schema guide](docs/user_guide.md)
- [Consultant-facing methodology note](docs/methodology_note.md)
- [Technical methodology](docs/methodology.md)
- [Technical handover](docs/handover.md)
- [S4 oral restitution script](docs/s4_restitution.md)

## Quality

```bash
ruff check .
ruff format --check .
pytest -v
pytest --cov=monte_carlo_simulator --cov-report=term-missing --cov-fail-under=85
mypy src/monte_carlo_simulator
```

Frontend type/build check:

```bash
cd web
npm install
npm run build
```

## Simplified architecture

```text
web/                         React + TypeScript + Vite
          |
          v
src/monte_carlo_simulator/web_api.py
          |
          v
src/monte_carlo_simulator/application/
          |
          +--> engine / distributions / analysis / io

streamlit_app/               S4 fallback interface
scripts/
data/templates/
docs/
tests/
```

The interactive layers must remain thin: probabilistic rules belong in `src/monte_carlo_simulator`, not in Streamlit or React.

## Confidentiality

- Do not commit real risk registers without anonymization and authorization.
- Do not add client identifiers or personal data to examples or tests.
- `.xlsx` and `.xls` files remain ignored globally except for the public fictitious template explicitly allowed by the repository rules.

## Next extensions

The S5 comparison flow currently uses a modified Excel workbook as the what-if input. A later iteration can add direct browser editing of validated assumptions, plus PDF/PowerPoint decision exports and calibration from authorized historical data.
