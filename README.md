# Monte-Carlo-Simulator

A Python project for probabilistic project cost and schedule risk analysis with Monte Carlo simulation.

## 1. Project context
This repository hosts an academic project to model uncertainty on project costs/durations and support risk-informed decisions.

## 2. Objectives
- Build a layered and maintainable simulation architecture.
- Run vectorized Monte Carlo simulations with reproducible seeds.
- Provide statistical and visual outputs for project risk analysis.

## 3. Currently available features

- Layered project architecture with clear packages.
- Vectorized and reproducible Monte Carlo engine.
- Six distributions: triangular, Beta-PERT with configurable `lambda_shape`, uniform,
  normal, arithmetic-parameterized log-normal and Bernoulli × impact event risk.
- Deterministic handling of zero-width distributions, zero standard deviations and
  event probabilities equal to 0 or 1.
- Validation of required finite numeric parameters and strictly positive integer sample sizes.
- Case-insensitive distribution aliases and unique risk-item names after trimming.
- Heterogeneous cost or duration simulations with one vectorized draw per item.
- Versioned Excel risk-register schema `1.0`, documented template and aggregated validation errors.
- Optional Gaussian-copula correlations from a `correlations` Excel sheet using a strictly positive-definite matrix and Cholesky sampling.
- End-to-end Excel → `RiskItem` → simulation → CSV summary and histogram workflow.
- Summary statistics: mean, median, standard deviation, minimum, maximum and configurable
  collision-safe percentile labels such as P50, P95.1 and P99.5.
- Histogram export with percentile markers.
- CLI for both Excel inputs and the built-in demonstration; initial Streamlit skeleton.

### Distribution inputs

| Canonical name | Accepted aliases | Required parameters |
| --- | --- | --- |
| `triangular` | — | `minimum`, `most_likely`, `maximum` |
| `pert` | `beta-pert`, `beta_pert`, `beta pert` | `minimum`, `most_likely`, `maximum`; optional `lambda_shape` (default `4.0`) |
| `uniform` | — | `minimum`, `maximum` |
| `normal` | — | `mean`, `standard_deviation` |
| `lognormal` | `log-normal`, `log_normal`, `log normal` | arithmetic `mean`, arithmetic `standard_deviation` |
| `event` | `event-based`, `event_based`, `event based`, `eventual`, `bernoulli`, `bernoulli-event`, `bernoulli_event` | `probability`, `impact` |

Distribution identifiers are trimmed and case-insensitive. Finite negative values are valid for
three-point bounds, uniform bounds, normal means and event impacts. A log-normal mean must be
strictly positive; every standard deviation must be non-negative.

### Excel risk register

The public template is [`data/templates/risk_register_template.xlsx`](data/templates/risk_register_template.xlsx).
It contains fictitious examples for all six distributions, field instructions and simple Excel
drop-down lists. The required sheets are:

- `metadata`: schema and project-level key/value information;
- `risk_register`: one project item or event risk per row;
- `instructions`: documentation included for users of the template.

Schema `1.0` requires `analysis_type` to be `cost` or `duration`. Blank item units inherit
`default_unit`, and all active rows must resolve to the same unit. This prevents silent addition
of incompatible currencies or time units. `baseline_estimate` is an optional finite reference
value returned with the results; it is deliberately **not** added to the simulated total.

See [the user guide](docs/user_guide.md) for the complete schema and validation rules.

### Correlations

Add an optional `correlations` sheet to simulate dependencies between active items. The first row contains column item names, the first column contains row item names, and coefficients are aligned by name before validation. The matrix must cover exactly the active items, be square, symmetric, finite, bounded in `[-1, 1]`, have a unit diagonal and be strictly positive definite.

Generate the synthetic public workbook with `python scripts/generate_correlated_cost_register.py`; it writes `data/examples/correlated_cost_register.xlsx`, which remains ignored like other `.xlsx` files.

## 4. Planned features

- Tornado chart, S-curve and convergence diagnostics.
- Interactive Streamlit workflow.
- Scenario comparison and automated decision-ready exports.

## 5. Installation

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 6. Execution commands

Run the included Excel template:

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

The command writes `simulation_summary.csv` and `simulation_histogram.png`. Without `--input`,
the historical fictitious demonstration remains available:

```bash
python -m monte_carlo_simulator.cli
```

## 7. Test and quality commands

```bash
ruff check .
ruff format --check .
pytest -v
pytest --cov=monte_carlo_simulator --cov-report=term-missing --cov-fail-under=85
mypy src/monte_carlo_simulator
```

## 8. Simplified tree

```text
src/monte_carlo_simulator/
  models/ distributions/ engine/ analysis/ io/ visualization/ application/
tests/
data/input/ data/output/ data/templates/
streamlit_app/
```

## 9. Git conventions

- Keep small, focused commits.
- Add tests for new behavior.
- Preserve API compatibility when extending advanced features.

## 10. Confidentiality

- Do not commit real risk registers without anonymization and authorization.
- Do not add confidential project, personal or client data.
- `.xlsx` and `.xls` files remain ignored globally; only the public fictitious template is
  explicitly allowed by `.gitignore`.
