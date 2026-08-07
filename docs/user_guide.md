# User guide — Excel schema and execution reference

For a consultant-facing walkthrough, start with [`user_guide_30min.md`](user_guide_30min.md). This document is the detailed reference for the Excel schema, validation rules and available execution paths.

## Start from the template

Copy `data/templates/risk_register_template.xlsx` outside the repository before entering real project data. The committed workbook is fictitious and covers all six supported distributions.

The workbook schema is versioned. This guide describes schema `1.0`; an unsupported version is rejected instead of being guessed or migrated silently.

## `metadata` sheet

The sheet uses the headers `key` and `value`.

| Key | Required | Rule |
| --- | --- | --- |
| `schema_version` | yes | Text equal to `1.0` |
| `project_name` | yes | Non-empty text |
| `analysis_type` | yes | `cost` or `duration`, case-insensitive |
| `default_unit` | yes | Common currency or time unit such as `MAD`, `EUR`, `days` |
| `baseline_estimate` | no | Finite real number when supplied |
| `description` | no | Non-confidential text |

`baseline_estimate` is contextual information for comparison and reporting. It is **not** automatically added to simulated samples. If a deterministic amount must form part of the simulated total, represent it as an explicit active item.

## `risk_register` sheet

One row represents one cost/duration item or one event risk.

| Column | Value |
| --- | --- |
| `name` | Required non-empty item name, unique ignoring case and outer spaces |
| `distribution` | Required canonical name or supported alias |
| `minimum` | Minimum for triangular, PERT or uniform |
| `most_likely` | Mode for triangular or PERT |
| `maximum` | Maximum for triangular, PERT or uniform |
| `mean` | Arithmetic mean for normal or log-normal |
| `standard_deviation` | Arithmetic standard deviation for normal or log-normal |
| `probability` | Event probability in `[0, 1]` |
| `impact` | Deterministic event impact |
| `lambda_shape` | Optional positive PERT shape; blank means `4.0` |
| `category` | Optional descriptive category |
| `unit` | Optional row unit; blank inherits `default_unit` |
| `enabled` | Optional; blank means active, `FALSE` ignores the row |
| `notes` | Optional free text |

`enabled` and `notes` may be absent. Other schema columns must exist, although unused cells may remain blank.

### Required parameters by distribution

| Distribution | Required cells | Domain |
| --- | --- | --- |
| `triangular` | `minimum`, `most_likely`, `maximum` | `minimum <= most_likely <= maximum` |
| `pert` | `minimum`, `most_likely`, `maximum` | same ordering; optional `lambda_shape > 0` |
| `uniform` | `minimum`, `maximum` | `minimum <= maximum` |
| `normal` | `mean`, `standard_deviation` | `standard_deviation >= 0` |
| `lognormal` | `mean`, `standard_deviation` | arithmetic `mean > 0`, deviation `>= 0` |
| `event` | `probability`, `impact` | `probability` in `[0, 1]` |

Finite numeric Excel cells and finite numeric strings are accepted at the import boundary. Booleans, `NaN`, infinities and arbitrary text are not accepted as numeric parameters.

Finite negative values are allowed when mathematically meaningful, including a negative event impact representing an opportunity. They are not valid for a standard deviation, a PERT shape or a log-normal mean.

## Distribution aliases

Canonical names are `triangular`, `pert`, `uniform`, `normal`, `lognormal` and `event`.

Accepted aliases include:

- `beta-pert`, `beta_pert`, `beta pert` → `pert`;
- `log-normal`, `log_normal`, `log normal` → `lognormal`;
- `event-based`, `event_based`, `event based`, `eventual`, `bernoulli`, `bernoulli-event`, `bernoulli_event` → `event`.

Distribution names are trimmed and case-insensitive.

## Units

Every active row must resolve to one common unit. A blank row unit inherits `default_unit`; matching is case-insensitive. Registers mixing currencies or time units are rejected. The importer never performs exchange-rate or time-unit conversion.

Disabled rows are ignored before parameter and unit validation.

## Optional `correlations` sheet

The sheet defines a square matrix whose rows and columns are active item names. Row and column order may differ because alignment is performed by name before validation.

The matrix must:

- cover exactly the active items;
- be square and finite;
- be symmetric;
- contain coefficients in `[-1, 1]`;
- have a unit diagonal;
- be strictly positive definite.

The implementation uses a Gaussian copula with Cholesky decomposition. Invalid matrices are rejected. The application does not project, clip, jitter or otherwise repair a user matrix silently.

A valid correlated run writes `correlation_diagnostics.csv` with numerical health evidence and `automatic_repair_applied = False`.

## Run the Streamlit interface

Install UI dependencies and start the app:

```bash
pip install -e ".[ui]"
streamlit run streamlit_app/app.py
```

The interface provides:

- `.xlsx` upload;
- simulation count and seed controls;
- P50/P80/P90/P95 decision-level selector;
- interactive Plotly histogram and S-curve;
- baseline exceedance probability and reserve;
- interactive Spearman tornado;
- convergence view and correlation diagnostics;
- individual artifact downloads and a ZIP bundle.

Validation failures are displayed with workbook context whenever available.

## Run the CLI

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

Without `--input`, the built-in fictitious demonstration remains available:

```bash
python -m monte_carlo_simulator.cli
```

## Generated artifacts

A standard Excel run produces:

- `simulation_summary.csv` — mean, median, standard deviation, min/max and configured percentiles;
- `simulation_histogram.png` — static histogram with percentile markers;
- `simulation_s_curve.png` — empirical cumulative curve;
- `percentile_decision_table.csv` — percentile, exceedance probability, baseline gap and reserve where applicable;
- `convergence_diagnostics.csv` — cumulative stability of the target percentile;
- `sensitivity_summary.csv` — Spearman coefficient, absolute coefficient, rank and defined/undefined status;
- `sensitivity_tornado.png` — defined sensitivity rows ordered by importance.

Optional artifacts:

- `baseline_comparison.csv` when `baseline_estimate` exists;
- `correlation_diagnostics.csv` when a correlation matrix exists.

## Reading the Spearman outputs

The sensitivity table contains:

- `item_name`;
- `spearman_rho`;
- `absolute_rho`;
- `rank`;
- `direction`;
- `is_defined`;
- `undefined_reason`.

A deterministic input is constant, so its Spearman correlation is mathematically undefined. Such a row remains in the CSV with `undefined_reason = constant_input` and is excluded from the tornado by default.

With correlated inputs, Spearman remains descriptive. It is not a causal effect, not an additive variance decomposition and should not be normalized to sum to 100 %.

## Baseline comparison

When `baseline_estimate` is present, the workflow reports:

- the baseline;
- the simulated mean;
- strict `P(total > baseline)`;
- P50, P80 and P90;
- percentile gaps against baseline;
- relative gaps when the baseline is positive;
- non-negative reserves.

Equality with the baseline is not counted as an exceedance. Relative gaps are undefined for zero or negative baselines.

## Convergence

The convergence diagnostic recomputes the target percentile over cumulative blocks of samples. It tracks absolute and relative changes, counts consecutive stable blocks and can mark one recommended stopping point.

A stable percentile estimate indicates that the sample count is numerically adequate for that run. It does not validate the business assumptions in the workbook.

## Validation errors

The loader collects independent problems before failing. Common causes include:

- missing required worksheet, metadata key or column;
- unsupported schema version or distribution;
- blank or duplicate names;
- missing or invalid distribution parameters;
- invalid probability, standard deviation or PERT shape;
- incompatible units or no active rows;
- a missing, corrupt or non-`.xlsx` input;
- a malformed or non-positive-definite correlation matrix.

Programming exceptions are not converted into workbook validation messages.

## Reproducibility

Using the same workbook, active item order, simulation count, confidence levels and seed reproduces the same samples. For a decision trace, record at minimum the input identifier, repository commit, number of simulations and seed.

## Confidentiality

Real client and project registers must not be committed. Repository rules ignore `.xlsx` and `.xls` files except the public fictitious template. Keep real workbooks outside Git and only share anonymized data under the appropriate authorization.

## Current extension boundary

The S4 scope is implemented: Streamlit, tests/quality gate, user documentation, methodology note and handover material. Planned S5/S6 extensions include what-if analysis, scenario comparison, PDF/PowerPoint exports and calibration from authorized historical data.
