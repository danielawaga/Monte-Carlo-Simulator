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
- Strict correlation diagnostics with eigenvalue, condition-number and policy evidence; invalid matrices are rejected and never repaired silently.
- End-to-end Excel → `RiskItem` → simulation → decision artifacts workflow.
- Summary statistics: mean, median, standard deviation, minimum, maximum and configurable collision-safe percentile labels such as P50, P95.1 and P99.5.
- Histogram and empirical S-curve exports with percentile markers.
- Decision-oriented percentile table with exceedance probability, baseline gap and recommended reserve.
- Cumulative percentile convergence diagnostics with a recommended stable draw count.
- Spearman sensitivity analysis and tornado chart.
- Baseline comparison report with exceedance probability, percentile gaps and P80/P90 reserves.
- Reproducible synthetic S3 acceptance case and consultant-validation protocol.
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

Distribution identifiers are trimmed and case-insensitive. Finite negative values are valid for three-point bounds, uniform bounds, normal means and event impacts. A log-normal mean must be strictly positive; every standard deviation must be non-negative.

### Excel risk register

The public template is [`data/templates/risk_register_template.xlsx`](data/templates/risk_register_template.xlsx). It contains fictitious examples for all six distributions, field instructions and simple Excel drop-down lists. The required sheets are:

- `metadata`: schema and project-level key/value information;
- `risk_register`: one project item or event risk per row;
- `instructions`: documentation included for users of the template.

Schema `1.0` requires `analysis_type` to be `cost` or `duration`. Blank item units inherit `default_unit`, and all active rows must resolve to the same unit. This prevents silent addition of incompatible currencies or time units. `baseline_estimate` is an optional finite reference value returned with the results; it is deliberately **not** added to the simulated total.

See [the user guide](docs/user_guide.md) for the complete schema and validation rules.

### Correlations

Add an optional `correlations` sheet to simulate dependencies between active items. The first row contains column item names, the first column contains row item names, and coefficients are aligned by name before validation. The matrix must cover exactly the active items, be square, symmetric, finite, bounded in `[-1, 1]`, have a unit diagonal and be strictly positive definite.

The policy is deliberately strict: the application does not project, clip, jitter or otherwise repair the matrix. A rejected matrix reports its minimum eigenvalue so that the workbook can be corrected explicitly. Valid correlated runs create `correlation_diagnostics.csv` with the numerical health indicators and `automatic_repair_applied = False`.

Generate the synthetic public workbook with:

```bash
python -m scripts.generate_correlated_cost_register
```

It writes `data/examples/correlated_cost_register.xlsx`, which remains ignored like other generated `.xlsx` files.

## 4. Planned features

- Interactive Streamlit workflow.
- Scenario comparison and what-if mode.
- Automated PDF or PowerPoint decision exports.
- Calibration from authorized historical data.

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

The Excel workflow writes the histogram, S-curve, summary, percentile decision table, convergence diagnostics, Spearman sensitivity table and tornado chart. A correlated register also writes `correlation_diagnostics.csv`. When the workbook supplies `baseline_estimate`, the command additionally writes `baseline_comparison.csv`. The baseline remains contextual and is never added to simulated totals.

Without `--input`, the historical fictitious demonstration remains available:

```bash
python -m monte_carlo_simulator.cli
```

### Reproducible S3 acceptance case

Run the complete synthetic correlated workflow and generate a Markdown evidence report:

```bash
python -m scripts.run_s3_acceptance_case
```

The output is written under `data/output/s3_acceptance/`. The data is synthetic and explicitly non-representative; this command validates the software path and numerical invariants, not the credibility of real project assumptions. Use the [consultant workshop protocol](docs/consultant_validation_workshop.md) and the anonymized [decision-log template](data/templates/consultant_validation_log.csv) for field validation.

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
- `.xlsx` and `.xls` files remain ignored globally; only the public fictitious template is explicitly allowed by `.gitignore`.

## Analyse de sensibilité Spearman et tornado

Le workflow Excel produit `sensitivity_summary.csv` et `sensitivity_tornado.png`. Le tableau contient les colonnes `item_name`, `spearman_rho`, `absolute_rho`, `rank`, `direction`, `is_defined` et `undefined_reason`.

La sensibilité V1 utilise la corrélation de rang de Spearman entre les tirages de chaque poste (`SimulationResult.item_samples`) et le total simulé. Spearman mesure une association monotone par rangs : il est plus robuste que Pearson pour les distributions non normales, asymétriques ou événementielles avec de nombreux ex æquo. Les postes déterministes ont une corrélation mathématiquement indéfinie ; ils sont exportés avec `spearman_rho = NaN`, sans rang et `undefined_reason = constant_input`, puis exclus par défaut du tornado.

Le signe indique le sens de l'association monotone et la valeur absolue sert uniquement au classement. Lorsque des entrées sont corrélées, ces coefficients ne sont pas causaux, ne décomposent pas additivement la variance et ne doivent pas être normalisés pour sommer à 100 %.
