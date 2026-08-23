# Monte-Carlo-Simulator

Python application for probabilistic project cost and schedule risk analysis. The project turns an Excel risk register into a simulated total distribution, decision percentiles, baseline reserves, correlation diagnostics, convergence evidence and sensitivity outputs.

## Current status — S6 on-premises deployment

The simulator is deployed as an internal application: one instance on a machine of the company
network, reached from a browser, with real user accounts stored locally. The repository combines two
layers:

- a tested Python Monte Carlo engine, application service, HTTP API and local account store;
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
- local user accounts with two roles, `httpOnly` session cookies and a first-run administrator setup;
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

## Accounts and local deployment

The simulator runs as **one instance on a designated machine of the company network**. Members reach
it from a browser; nothing leaves the site. Identity is a real account, held in a local SQLite file.

### First launch

Start the API, open the interface, and the browser offers a **first-configuration screen** to create
the founding administrator. That screen closes permanently as soon as one account exists, so create
the administrator right after the first launch.

The database lives in a per-machine data directory — `%LOCALAPPDATA%\MonteCarloSimulator` on Windows,
`~/.local/share/MonteCarloSimulator` elsewhere — and never inside the application tree, so a packaged
executable can unpack itself read-only. Override it with `MCS_DATA_DIR`:

```bash
export MCS_DATA_DIR=/srv/monte-carlo
uvicorn monte_carlo_simulator.web_api:app --host 0.0.0.0 --port 8000
```

That one file is the whole state of the installation: **back it up and you have backed up everything.**

### Roles

Two roles. `member` uses the simulator; `admin` also manages accounts from `/administration`.
Everyone sees the same registers and results — the shared-work and traceability requirement, not
per-person isolation — while authorship is recorded. The last active administrator can be neither
disabled nor demoted, so an installation can never become unadministrable.

### Shared registers and runs

Registers and completed runs live in the same database and are **shared by everyone**: any signed-in
member sees every register, can pick up a colleague's work and continue it. That is the point of the
single instance — no more mailing spreadsheets around.

Authorship is recorded on every write and never used to hide anything. A register keeps both who
created it and who last changed it, so a reserve figure that went to a client can be traced back to
the person who produced it.

Two deliberate asymmetries:

- **deleting a register is reserved to administrators.** Editing is everyone's business; destroying
  shared assumptions is not;
- **runs outlive their register.** Deleting a register detaches its runs rather than erasing them —
  a decision record that can quietly disappear is not a decision record. Authorship likewise
  outlives the account: a removed user leaves their work behind, attributed to « Compte supprimé ».

### Sessions

Sign-in returns an `httpOnly` session cookie, so page scripts cannot read the token. Sessions expire
after 12 hours. Changing a password or disabling an account closes every open session immediately.
Passwords are hashed with `hashlib.scrypt`; only the hash of a session token is stored, so a stolen
copy of the database cannot be replayed as a live session.

### Two deployment cautions

**The listening interface.** `--host 0.0.0.0` exposes the service to everything on the subnet,
including the guest wifi if the network is flat. Bind to a specific address when that matters, and
expect Windows Firewall to ask for permission the first time.

**Plain HTTP.** Over a wired LAN in a closed office the risk is low. **On wifi it is not**: passwords
and risk registers travel in clear and anyone on the same network can read them. Put the service
behind TLS — an internal certificate authority, or a self-signed certificate accepted once per
machine — before relying on it over wireless.

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
- The account database holds password hashes and session tokens: back up `MCS_DATA_DIR` like any other confidential asset, and never commit it.
- Serve the interface over TLS before exposing it on wireless, where credentials would otherwise travel in clear.

## Next steps

Priority work for the end of S5 / beginning of S6:

- preserve imported correlation matrices through the editable-hypotheses workflow;
- connect the React service layer to the Python backend while keeping the simulation engine unchanged;
- consolidate direct what-if editing and scenario comparison;
- finalize user documentation and handover;
- optional PDF/PowerPoint decision exports;
- calibration from authorized historical project data if such data become available.
