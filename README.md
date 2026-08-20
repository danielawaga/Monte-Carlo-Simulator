# Monte-Carlo-Simulator

Python application for probabilistic project cost and schedule risk analysis. The project turns an Excel risk register into a simulated total distribution, decision percentiles, baseline reserves, correlation diagnostics, convergence evidence and sensitivity outputs.

## Current status — S5 interface & what-if workflow

The repository now combines three layers:

- a tested Python Monte Carlo engine and application service;
- the operational Streamlit interface used to import, edit and simulate risk assumptions;
- a React + TypeScript + Vite interface under `web/`, structured around Configuration, Results and Scenario Comparison views.

The S5 work focuses on making the simulator easier to explore and use interactively without moving probabilistic logic out of Python.

### Available features

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
- interactive Plotly visualizations with exact values on hover;
- editable assumptions after Excel import in the Streamlit workflow;
- reset/re-run workflow for lightweight what-if analysis;
- React/TypeScript/Vite frontend with a risk-register builder, unified Simulation/Scenarios workspace and Results screen;
- reproducible synthetic acceptance case and consultant-validation protocol;
- user, methodology, handover and restitution documentation.

## Installation

Python 3.11+ is required.

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,ui]"
```

## Streamlit interface — operational workflow

```bash
streamlit run streamlit_app/app.py
```

The Streamlit application currently provides the complete end-to-end simulation path. A consultant can:

1. upload a schema-1.0 `.xlsx` risk register;
2. import its assumptions into an editable table;
3. modify distributions and parameters directly from the interface;
4. reset the assumptions to the imported state;
5. validate the edited register before simulation;
6. choose simulation count, seed and decision confidence level;
7. inspect interactive Plotly views of the distribution and empirical S-curve;
8. inspect Spearman sensitivity and the tornado view;
9. read P50/P80/P90/P95, baseline exceedance probability and reserve;
10. download the generated decision artifacts.

Start with [`docs/user_guide_30min.md`](docs/user_guide_30min.md).

## React / TypeScript interface — S6 integrated workflow

The `web/` directory contains the S5 frontend built with React, TypeScript and Vite.

Main routes:

- `/risques` — project, risk items, distributions, correlations, validation and Excel export;
- `/configuration` — simulation preparation;
- `/resultats` — results analysis;
- `/comparaison` — detailed comparison of a frozen reference and the current run, linked from Results;
- `/scenarios` — compatibility redirect to the Scenarios tab in `/configuration`.

Install the Python web dependencies and start the API from the repository root:

```bash
pip install -e ".[web]"
uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
cd web
npm install
npm run dev
```

Production build:

```bash
npm run build
```

The `/risques` route builds or imports a schema-1.0 register, validates it through the Python engine and exports a compatible `.xlsx`, including an optional correlation matrix. `/configuration` reuses that shared register, groups execution standards and scenario documentation on one screen, and sends the draft directly to the API. `/resultats` displays the resulting indicators, histogram, S-curve and sensitivity ranking. The API delegates all probabilistic rules to `run_simulation_from_excel`; React remains responsible for editing, presentation and local scenario snapshots. Secondary workspace views still use demonstration data.

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

## Interactive decision views

### Distribution

The histogram exposes the simulated intervals and counts on hover and displays the selected percentile markers.

### Empirical S-curve

The cumulative curve exposes cost and cumulative probability on hover, making it possible to read both:

- the probability of remaining below a given budget;
- the budget associated with a chosen confidence level.

### Sensitivity

Spearman rank sensitivity identifies the assumptions with the strongest monotonic relationship to the simulated total and feeds the tornado view.

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

## Reproducible validation path

Generate and execute the synthetic correlated acceptance case with:

```bash
python -m scripts.run_s3_acceptance_case
```

Outputs are written under `data/output/s3_acceptance/`. This case validates the software path and numerical invariants; it does not validate the credibility of a real client's assumptions.

For field validation, use:

- [`docs/consultant_validation_workshop.md`](docs/consultant_validation_workshop.md);
- [`data/templates/consultant_validation_log.csv`](data/templates/consultant_validation_log.csv).

## Quality

```bash
ruff check .
ruff format --check .
pytest -v
pytest --cov=monte_carlo_simulator --cov-report=term-missing --cov-fail-under=85
mypy src/monte_carlo_simulator
```

Frontend build:

```bash
cd web
npm install
npm run build
```

## Simplified architecture

```text
web/                         React + TypeScript + Vite frontend

streamlit_app/               Operational interactive interface
        |
        v
src/monte_carlo_simulator/
  application/               Application orchestration
  models/                    Domain models
  distributions/             Supported probability laws
  engine/                    Monte Carlo execution
  analysis/                  Percentiles, sensitivity, convergence
  io/                        Excel schema, validation and exports
  visualization/             Static/export visualizations

tests/
scripts/
data/templates/
docs/
```

The interactive layers must remain thin: probabilistic rules belong in `src/monte_carlo_simulator`, not in Streamlit or React components.

## Documentation

- [30-minute user guide](docs/user_guide_30min.md)
- [Detailed Excel/schema guide](docs/user_guide.md)
- [Consultant-facing methodology note](docs/methodology_note.md)
- [Technical methodology](docs/methodology.md)
- [Technical handover](docs/handover.md)
- [S4 oral restitution script](docs/s4_restitution.md)
- [React frontend notes](web/README.md)

## Known limitation

The current editable-hypotheses adapter exposes imported metadata and risk rows, but correlation matrices require special care when regenerating an edited workbook. Until this path is fully preserved end-to-end, correlated workbooks should be validated after editing to ensure the `correlations` sheet has not been lost.

## Confidentiality

- Do not commit real risk registers without anonymization and authorization.
- Do not add client identifiers or personal data to examples or tests.
- `.xlsx` and `.xls` files remain ignored globally except for the public fictitious template explicitly allowed by the repository rules.

## Next steps

Priority work for the end of S5 / beginning of S6:

- preserve imported correlation matrices through the editable-hypotheses workflow;
- connect the React service layer to the Python backend while keeping the simulation engine unchanged;
- consolidate direct what-if editing and scenario comparison;
- finalize user documentation and handover;
- optional PDF/PowerPoint decision exports;
- calibration from authorized historical project data if such data become available.
