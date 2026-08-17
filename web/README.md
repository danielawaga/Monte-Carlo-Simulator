# S5 React interface

This directory contains the consultant-facing interface introduced in week 5. It replaces the UI role previously held only by Streamlit while keeping the existing Python simulation engine as the single source of probabilistic rules.

## Development

From the repository root:

```bash
pip install -e ".[web]"
uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

Then in a second terminal:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`.

## Production build

```bash
cd web
npm install
npm run build
cd ..
uvicorn monte_carlo_simulator.web_api:app --host 0.0.0.0 --port 8000
```

When `web/dist` exists, FastAPI serves the compiled single-page application directly.

## Scope

The S5 interface provides:

- drag-and-drop Excel upload;
- simulation count, seed and confidence-level selection;
- P50/P80/P90/P95 decision metrics;
- browser-native histogram and empirical S-curve;
- Spearman sensitivity ranking;
- baseline exposure reading;
- scenario comparison by freezing a reference run, changing the workbook and re-running;
- responsive layout for desktop and tablet use.

The API adapter is intentionally thin. It calls `run_simulation_from_excel`; it does not duplicate distributions, correlation logic, convergence rules or sensitivity calculations.
