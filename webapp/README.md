# OpenPKFlow Web App

Modern React (Vite + TypeScript + Tailwind) frontend for the OpenPKFlow pharmacometric engine.
All calculations run in the FastAPI backend — the frontend only renders results and charts.

## Stack

- **Vite + React 19 + TypeScript**
- **Tailwind CSS** — dark enterprise theme (`--bg: #0e0f11`, accent `#5e6ad2`)
- **Recharts** — concentration-time and dissolution profile charts (linear/semi-log toggle)
- **TanStack Query** — data fetching and cache
- **react-router-dom** — SPA routing

## Modules

| Page | Path | Features |
|------|------|---------|
| Home | `/` | Module overview cards |
| NCA | `/nca` | CSV upload, column mapping, AUC/Cmax/Tmax/t½ metrics, per-subject chart, report download |
| Sparse NCA | `/nca/sparse` | Model-informed oral fit, published example, diagnostics, observed/fitted chart, HTML/Markdown reports |
| Dissolution | `/dissolution` | Single/multi-media comparison plus Advanced Workbench with vessel plots, bootstrap f2, five-model ranking, reports, and audit ZIP |
| Simulation | `/sim` | Interactive parameter sliders, live PK curve (debounced), multi-dose, report download |
| IVIVC | `/ivivc` | Wagner-Nelson/Loo-Riegelman inputs, example data, predictability results, reports |
| Bioequivalence | `/be` | Paired TOST analysis plus exact power and sample-size calculator |
| Formal BE ANOVA | `/be/anova` | Complete balanced TR/RT long-format formal 2x2 ANOVA with ANOVA table and reports |
| FDA RSABE | `/be/rsabe` | Validated balanced TRR/RTR/RRT partial-replicate analysis and reports |
| Study Pipeline | `/pipeline` | Optional dissolution/NCA/BE stages, unified results, report and audit ZIP downloads |
| MAP Individual PK | `/bayes/map` | Oral and IV-bolus MAP screening with diagnostics and reports |
| SUPAC & Alcohol | `/supac` | SUPAC-IR change classification and alcohol dose-dumping f2 screening |

## Setup

```bash
# The FastAPI backend must be running on port 8000 (see api/README.md)
cd webapp
npm install
npm run dev        # Vite dev server -> http://localhost:5173
npm run build      # Production build -> dist/
```

Vite proxies `/api` and `/health` to `http://localhost:8000` automatically.

For a deployed backend, set `VITE_API_URL` before the production build. The frontend
contains no pharmacometric formulas; all calculations and report generation are delegated
to the FastAPI adapter and `src/openpkflow/`.

Production uses `VITE_API_URL=https://openpkflow.onrender.com`. The Cloudflare
frontend, documentation, and Render backend were verified after v2.8.0
publication. Render reports version 2.8.0 from `main`; its `/health` payload is
the source of truth for the current deployed commit. See the evidence in the
root `HANDOFF.md`.
