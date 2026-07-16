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
- Six distributions: triangular, Beta-PERT, uniform, normal, log-normal and event-based.
- Validation of distribution parameters and unique risk-item names.
- 10,000+ simulations on heterogeneous cost or duration items.
- Summary statistics: mean, median, std, min, max, P50, P80, P90.
- Histogram export with percentile markers.
- Basic CLI and initial Streamlit skeleton.

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
pytest
ruff check .
ruff format --check .
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
