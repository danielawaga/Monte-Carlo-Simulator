# Monte-Carlo-Simulator

Python application for probabilistic project cost and schedule risk analysis. The project turns an Excel risk register into a simulated total distribution, decision percentiles, baseline reserves, correlation diagnostics, convergence evidence and sensitivity outputs.

## Current status — S4 usability

The repository now contains a complete consultant-facing Streamlit workflow in addition to the CLI and Python application service.

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
- interactive Streamlit upload, simulation, Plotly charts, confidence selector and downloadable artifact bundle;
- reproducible synthetic acceptance case and consultant-validation protocol;
- user, methodology, handover and restitution documentation.

## Installation

Python 3.11+ is required.

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,ui]"
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,ui]"
```

## Streamlit interface

```bash
streamlit run streamlit_app/app.py
```

The interface lets a consultant:

1. upload a schema-1.0 `.xlsx` risk register;
2. choose the simulation count and seed;
3. choose P50, P80, P90 or P95 as the decision level;
4. inspect the interactive distribution and S-curve;
5. read the baseline exceedance probability and reserve;
6. inspect Spearman sensitivity and convergence;
7. download every generated artifact or one ZIP bundle.

Start with [`docs/user_guide_30min.md`](docs/user_guide_30min.md).

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

The repository also runs these checks on pull requests through GitHub Actions.

## Simplified architecture

```text
src/monte_carlo_simulator/
  models/
  distributions/
  engine/
  analysis/
  io/
  visualization/
  application/
streamlit_app/
tests/
scripts/
data/templates/
docs/
```

The interactive layer must remain thin: probabilistic rules belong in `src/monte_carlo_simulator`, not in Streamlit.

## Confidentiality

- Do not commit real risk registers without anonymization and authorization.
- Do not add client identifiers or personal data to examples or tests.
- `.xlsx` and `.xls` files remain ignored globally except for the public fictitious template explicitly allowed by the repository rules.

## Next extensions

Weeks 5–6 are reserved for user feedback and optional extensions: what-if mode, scenario comparison, PDF/PowerPoint decision exports and calibration from authorized historical data.
