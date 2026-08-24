# Monte-Carlo-Simulator

Python application for probabilistic project cost and schedule risk analysis. The project turns an Excel risk register into a simulated total distribution, decision percentiles, baseline reserves, correlation diagnostics, convergence evidence and sensitivity outputs.

## Current status — S6 per-desk application

The simulator is installed on each desk and listens on the loopback interface only: nothing travels
over the network. The repository combines two layers:

- a tested Python Monte Carlo engine, application service, HTTP API and local store;
- a React + TypeScript + Vite interface under `web/`, the single operational interface, structured around Risk register, Configuration, Results and Scenario Comparison views.

The Streamlit interface that carried the S4/S5 workflow has been removed: React now covers the whole end-to-end path — import, edit, reset to the imported assumptions, validate, simulate, analyse and export — and adds scenario comparison, which Streamlit never had. The probabilistic logic stays in Python.

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
- interactive charts with exact values on hover, rendered as SVG by the React interface;
- editable assumptions after Excel import, with a one-click reset back to the imported register;
- reset/re-run workflow for lightweight what-if analysis;
- React/TypeScript/Vite frontend with a risk-register builder, unified Simulation/Scenarios workspace and Results screen;
- reproducible synthetic acceptance case and consultant-validation protocol;
- registers and completed runs saved in a local database, with the assumptions behind each figure;
- user, methodology, handover and restitution documentation.

## Installation

Python 3.11+ is required.

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,web]"
```

## React / TypeScript interface — the operational workflow

The `web/` directory contains the frontend built with React, TypeScript and Vite. It is the only interface: there is no second UI to keep in sync.

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

## Per-desk installation

Each desk runs its own copy. The launcher binds to `127.0.0.1` by default, so **nothing travels over
the network**: no password, no data, nothing to intercept. That is a deliberate reversal of an
earlier design — a single shared instance on the company network — which was dropped because
protecting it properly needed a TLS certificate that could not be installed on locked-down
workstations. Removing the network removes the problem rather than papering over it.

Colleagues exchange work the way they always did: through the `.xlsx` import and export.

### Launching it

Once the interface is built (`cd web && npm run build`), the API serves it from the same process, so
there is a single thing to start:

```bash
monte-carlo-simulator          # picks a free port, opens the browser
```

The launcher takes the first free port at or after 8000, so a second launch does not fail with a
stack trace on a machine nobody is watching.

**The listening address is fixed to `127.0.0.1` and cannot be changed from the command line.** The
application has no authentication — that went with the shared deployment — so any other bind address
would let every device on the subnet list, overwrite and delete the saved registers. TLS would not
make that safe: it encrypts the connection, it does not decide who may use it. Reaching the tool from
another machine would need an authentication layer back, which is a deliberate change and not a flag.

### A double-clickable executable

`packaging/monte-carlo-simulator.spec` bundles the interpreter, the server, the built interface and
the blank workbook into one file. The `Executable` workflow builds it on Windows — on demand or on a
`v*` tag — smoke-tests that the binary actually serves `/api/health` and the interface, then
publishes it as an artifact.

```bash
cd web && npm run build && cd ..
pip install -e ".[web,packaging]"
pyinstaller packaging/monte-carlo-simulator.spec
```

The console window is kept on purpose: it prints the address, and a startup failure stays readable
instead of the window vanishing.

**Verified on Linux, not on Windows.** The spec was exercised end to end here — building the binary,
launching it with no Python or Node available to it, and driving the whole path in a browser. The
Windows build itself runs in CI and has not been executed by the author.

### Saved registers and run history

Registers and completed runs live in a local SQLite file rather than in `localStorage`, which
vanishes with the browsing data and cannot be backed up. A fifth tab of `/risques` — **Enregistrés**
— lists them, saves the current draft and reopens one. Keeping a completed simulation is one button
on the Results screen; the run records its assumptions and the register it came from, which is what
lets a reserve figure sent to a client be traced back.

Deleting a register detaches its runs rather than erasing them: a decision record that can quietly
disappear is not a decision record.

The database lives in a per-machine data directory — `%LOCALAPPDATA%\MonteCarloSimulator` on Windows,
`~/.local/share/MonteCarloSimulator` elsewhere — and never inside the application tree, so a packaged
executable can unpack itself read-only. Override it with `MCS_DATA_DIR`. **That one file is the whole
state of the installation: back it up and you have backed up everything.**

An installation created by either earlier version upgrades in place: the accounts, the password
hashes and the session tokens are dropped — including from a version-1 database, which held accounts
and no registers at all — while the saved registers and their run history are kept.

### What this does not protect

The database sits on the disk, readable by anyone with the machine's session. There is no login
screen, and adding one would not change that — it would guard the interface, not the file. What
actually protects it is full-disk encryption such as BitLocker.

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

- [`docs/archive/consultant_validation_workshop.md`](docs/archive/consultant_validation_workshop.md);
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
        |
        v  HTTP (src/monte_carlo_simulator/web_api.py)
        |
src/monte_carlo_simulator/
  application/               Application orchestration
  models/                    Domain models
  distributions/             Supported probability laws
  engine/                    Monte Carlo execution
  analysis/                  Percentiles, sensitivity, convergence
  io/                        Excel schema, validation and exports
  visualization/             Static/export visualizations

tests/                       unit/ and integration/ suites
scripts/                     register generators and case-study tooling
data/
  templates/                 public fictitious workbooks
  input/                     sample inputs
  output/                    runtime outputs — generated, never versioned
docs/
  guides/                    how to run and hand over the project
  reference/                 architecture, methodology, documented case
  validation/                published validation evidence
  archive/                   dated deliverables kept as-is
reports/                     generated deliverables (S5 report, case study)
```

Two directory names carry a deliberate distinction: `data/output/` holds everything a run
generates and is never versioned, while `reports/` holds the finished deliverables that are.

The interactive layer must remain thin: probabilistic rules belong in `src/monte_carlo_simulator`, not in React components.

## Documentation

Start from the [documentation index](docs/README.md).

- [30-minute user guide](docs/guides/user_guide_30min.md)
- [Detailed Excel/schema guide](docs/guides/user_guide.md)
- [Technical handover](docs/guides/handover.md)
- [Consultant-facing methodology note](docs/reference/methodology_note.md)
- [Technical methodology](docs/reference/methodology.md)
- [Architecture](docs/reference/architecture.md)
- [React frontend notes](web/README.md)
- [Dated deliverables and working notes](docs/archive/)

## Known limitation

The current editable-hypotheses adapter exposes imported metadata and risk rows, but correlation matrices require special care when regenerating an edited workbook. Until this path is fully preserved end-to-end, correlated workbooks should be validated after editing to ensure the `correlations` sheet has not been lost.

## Confidentiality

- Do not commit real risk registers without anonymization and authorization.
- Do not add client identifiers or personal data to examples or tests.
- `.xlsx` and `.xls` files remain ignored globally except for the public fictitious template explicitly allowed by the repository rules.
- The local database holds client risk registers: back up `MCS_DATA_DIR` like any other confidential asset, never commit it, and rely on full-disk encryption to protect it at rest.
- The service binds to `127.0.0.1` and cannot be reconfigured: without authentication, any network bind would expose the registers to the whole subnet.

## Next steps

Priority work for the end of S5 / beginning of S6:

- preserve imported correlation matrices through the editable-hypotheses workflow;
- connect the React service layer to the Python backend while keeping the simulation engine unchanged;
- consolidate direct what-if editing and scenario comparison;
- finalize user documentation and handover;
- optional PDF/PowerPoint decision exports;
- calibration from authorized historical project data if such data become available.
