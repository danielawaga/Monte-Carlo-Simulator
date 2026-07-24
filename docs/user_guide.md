# User guide

## Start from the template

Copy `data/templates/risk_register_template.xlsx` outside the repository before entering real
project data. The committed file contains fictitious examples for all six supported
distributions. Microsoft Excel is not required by the application: `.xlsx` files are read and
written with `openpyxl`.

The workbook schema is versioned. This guide describes schema `1.0`; any other value is rejected
instead of being guessed or migrated silently.

## `metadata` sheet

The sheet uses the headers `key` and `value`. All six keys must be present. A value marked
optional may have an empty cell.

| Key | Required value | Rule |
| --- | --- | --- |
| `schema_version` | yes | Text equal to `1.0` |
| `project_name` | yes | Non-empty text |
| `analysis_type` | yes | `cost` or `duration`, case-insensitive |
| `default_unit` | yes | Common currency or time unit, for example `EUR`, `MAD`, `USD`, `days` or `hours` |
| `baseline_estimate` | no | Finite real number when supplied; booleans, NaN and infinities are invalid |
| `description` | no | Non-confidential text |

`baseline_estimate` is contextual information for comparison and reporting. It is returned in
the workflow metadata but is not automatically added to the simulated samples. To model a
deterministic amount in the simulated total, add an explicit active row, such as a uniform row
whose minimum equals its maximum. This explicit rule avoids counting a baseline twice.

## `risk_register` sheet

One row represents one cost/duration item or one event risk. These columns form schema `1.0`:

| Column | Value |
| --- | --- |
| `name` | Required non-empty item name; unique without regard to case or outer spaces |
| `distribution` | Required canonical name or supported alias |
| `minimum` | Minimum for triangular, PERT or uniform |
| `most_likely` | Mode for triangular or PERT |
| `maximum` | Maximum for triangular, PERT or uniform |
| `mean` | Arithmetic mean for normal or log-normal |
| `standard_deviation` | Arithmetic standard deviation for normal or log-normal |
| `probability` | Event occurrence probability in `[0, 1]` |
| `impact` | Deterministic event impact |
| `lambda_shape` | Optional positive PERT shape; blank means `4.0` |
| `category` | Optional descriptive category |
| `unit` | Optional row unit; blank inherits `default_unit` |
| `enabled` | Optional column and value; blank means `TRUE`, `FALSE` ignores the row |
| `notes` | Optional column and free text |

The columns `enabled` and `notes` may be absent. Every other column must exist, although cells
that are unused by a row's distribution may stay empty. Extra workbook columns are ignored.

### Required parameters by distribution

| Distribution | Required cells | Domain |
| --- | --- | --- |
| `triangular` | `minimum`, `most_likely`, `maximum` | `minimum <= most_likely <= maximum` |
| `pert` | `minimum`, `most_likely`, `maximum` | Same ordering; optional `lambda_shape > 0`, default `4.0` |
| `uniform` | `minimum`, `maximum` | `minimum <= maximum` |
| `normal` | `mean`, `standard_deviation` | `standard_deviation >= 0` |
| `lognormal` | `mean`, `standard_deviation` | Arithmetic `mean > 0`, arithmetic `standard_deviation >= 0` |
| `event` | `probability`, `impact` | `probability` in `[0, 1]` |

Supported aliases are documented in `docs/methodology.md`. Numeric Excel cells and finite numeric
strings such as `"125.5"` are accepted. Booleans are never accepted as numbers. Empty cells,
`NaN` values and whitespace-only strings are treated as blank. Strings representing `NaN` or an
infinity are invalid.

Finite negative values are allowed where they have a valid interpretation, including an event
opportunity with a negative impact. They are not allowed for a standard deviation, a PERT shape,
or a log-normal mean. Normal, triangular and uniform rows can produce or contain negative values.

## Units

Every active row must resolve to one common unit. A blank row unit inherits `default_unit`;
matching is case-insensitive. A register containing `EUR` and `USD`, `MAD` and `EUR`, or `days`
and `hours` is rejected. The importer never performs exchange-rate or time-unit conversion.
Disabled rows are ignored before parameter and unit validation.

## Run the CLI

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

The output directory receives:

- `simulation_summary.csv`, with moments and configured percentiles;
- `simulation_histogram.png`, with percentile markers.

Using the same workbook, item order, simulation count, confidence levels and seed reproduces the
same samples. Omitting `--input` preserves the built-in demonstration and writes
`triangular_histogram.png`.

## Validation errors

The loader collects independent problems before failing. Row problems include the worksheet,
Excel row number, item name when available, field and rejected value. Common causes include:

- missing `metadata` or `risk_register` sheet;
- missing required column or metadata key;
- unsupported schema version or distribution;
- blank or duplicate item names;
- missing distribution parameters or invalid parameter ordering;
- a boolean, non-numeric text, NaN or infinity used as a number;
- probability outside `[0, 1]`, negative deviation or non-positive PERT shape;
- incompatible units or no active rows;
- a missing, corrupt or non-`.xlsx` input file.

For correlated simulations, add a `correlations` sheet with active item names on both axes and finite coefficients in `[-1, 1]`; row and column order may differ. Fix every reported issue and run the command again. Programming exceptions are not converted into
workbook validation messages.

## Confidentiality

Real client and project registers must not be committed. Repository rules ignore all `.xlsx` and
`.xls` files except the single public template. Keep actual workbooks outside Git, remove personal
or client identifiers from test cases, and only share anonymized data under the appropriate
authorization.

## Current interface scope

The CLI and Python application service support the complete schema-v1 workflow. The Streamlit
directory remains an informational skeleton; a complete Streamlit interface is not implemented.
sensitivity analysis, tornado charts,
automatic convergence, scenario comparison, and PDF/PowerPoint export remain outside this scope.

## Reading the Spearman sensitivity outputs

After an Excel run, open `sensitivity_summary.csv` to review item-level sensitivity. The CSV
columns are:

- `item_name`: risk item name from the workbook.
- `spearman_rho`: Spearman rank correlation with the total, between -1 and 1 when defined.
- `absolute_rho`: absolute coefficient used for ordering importance.
- `rank`: 1 for the strongest defined association; blank for undefined items.
- `direction`: `positive`, `negative`, `neutral` or `undefined`.
- `is_defined`: whether the coefficient is interpretable.
- `undefined_reason`: for example `constant_input` for deterministic columns.

`sensitivity_tornado.png` visualizes the defined rows horizontally around zero. Bars to the
right are positive associations and bars to the left are negative associations; the most
important defined item appears at the top. Constant deterministic items are excluded from
this chart by default but remain visible in the CSV.

Use the tornado as a screening and prioritization aid. For correlated inputs, do not read
the ranking as causality or as a percentage contribution to total variance.

## Planned features

Future work still includes convergence diagnostics, S-curves, Streamlit exploration and
scenario comparison. Spearman sensitivity analysis and the tornado chart are now available
in the Excel workflow.

## Baseline comparison report

When `baseline_estimate` is present, the Excel workflow creates
`baseline_comparison.csv`. It contains the baseline, simulated mean, P50, P80 and P90, the
strict exceedance probability, absolute and relative percentile gaps, and non-negative
percentile reserves. Equality with the baseline is not an exceedance. Relative gaps are left
undefined for zero or negative baselines. If the metadata value is absent, this optional
artifact is not created.
