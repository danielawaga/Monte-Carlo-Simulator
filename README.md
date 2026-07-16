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
- Summary statistics: mean, median, std, min, max, P50, P80, P90.
- Histogram export with percentile markers.
- Basic CLI and initial Streamlit skeleton.

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

## 4. Planned features
- Excel risk register ingestion, schema validation and workbook template.
- Correlations with Cholesky decomposition.
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
```bash
python -m monte_carlo_simulator.cli
```

## 7. Test and quality commands
```bash
ruff check .
ruff format --check .
pytest -v
pytest --cov=monte_carlo_simulator --cov-report=term-missing
mypy src/monte_carlo_simulator
```

## 8. Simplified tree
```text
src/monte_carlo_simulator/
  models/ distributions/ engine/ analysis/ io/ visualization/ application/
tests/
data/input/ data/output/
streamlit_app/
```

## 9. Git conventions
- Keep small, focused commits.
- Add tests for new behavior.
- Preserve API compatibility when extending advanced features.

## 10. Confidentiality
- Do not commit real risk registers without anonymization and authorization.
- Do not add confidential project, personal or client data.
