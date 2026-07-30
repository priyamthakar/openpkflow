# OpenPKFlow Web API

FastAPI service that wraps the `openpkflow` Python engine and exposes REST endpoints
for the React frontend. **Contains no pharmacometric math** — every endpoint calls the
validated public APIs in `src/openpkflow/`.

## Setup

```bash
# From the repo root — install the engine first:
pip install -e ".[reports]"

# Install API deps:
cd api
pip install -r requirements.txt

# Run (dev, auto-reload):
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness + engine version |
| POST | `/api/nca/analyze` | Run NCA on uploaded CSV |
| POST | `/api/nca/report` | Download NCA report (html/pdf/docx/md) |
| POST | `/api/nca/sparse/analyze` | Fit a model-informed 1-cmt oral sparse profile |
| POST | `/api/nca/sparse/report` | Download sparse-fit screening report (html/md) |
| POST | `/api/dissolution/formulations` | List formulation labels from CSV |
| POST | `/api/dissolution/compare` | f1/f2 comparison |
| POST | `/api/dissolution/report` | Download dissolution report |
| POST | `/api/dissolution/multi-media/analyze` | Compare profiles across media |
| POST | `/api/dissolution/multi-media/report` | Download multi-media report |
| POST | `/api/dissolution/workbench/analyze` | Run the Advanced Dissolution Workbench |
| POST | `/api/dissolution/workbench/report` | Download complete workbench report |
| POST | `/api/dissolution/workbench/audit-bundle` | Download normalized inputs, results, report, and SHA-256 manifest |
| POST | `/api/sim/simulate` | Run PK simulation (JSON body) |
| POST | `/api/sim/report` | Download sim report |
| POST | `/api/ivivc/analyze` | Run Level A IVIVC analysis |
| POST | `/api/ivivc/report` | Download IVIVC report |
| POST | `/api/be/analyze` | Run paired 2x2 TOST screening |
| POST | `/api/be/report` | Download BE report |
| POST | `/api/be/anova/analyze` | Run formal complete balanced TR/RT 2x2 ANOVA |
| POST | `/api/be/anova/report` | Download formal ANOVA report |
| POST | `/api/be/rsabe/analyze` | Run validated balanced FDA partial-replicate RSABE |
| POST | `/api/be/rsabe/report` | Download FDA RSABE report |
| POST | `/api/be/power` | Calculate exact TOST power |
| POST | `/api/be/sample-size` | Calculate exact TOST sample size |
| POST | `/api/bayes/map/analyze` | Run MAP individual PK screening |
| POST | `/api/bayes/map/report` | Download MAP PK screening report |
| POST | `/api/supac/classify` | Screen a SUPAC-IR composition change level |
| POST | `/api/supac/alcohol` | Screen alcohol dose-dumping risk by f2 |
| POST | `/api/pipeline/analyze` | Run optional dissolution, NCA, and BE stages |
| POST | `/api/pipeline/report` | Download unified pipeline report |
| POST | `/api/pipeline/audit-bundle` | Download inputs, config, results, report, and manifest ZIP |

Sparse NCA is a model-informed screening fit, not a replacement for standard NCA or
a primary regulatory analysis. Endpoint responses and generated reports preserve that
scope caveat.

Formal ANOVA accepts long-format complete balanced 2x2 data with `subject`, `sequence`,
`period`, `treatment`, and the endpoint column. It fails closed for incomplete or
unbalanced designs. FDA partial-replicate RSABE supports complete balanced
TRR/RTR/RRT allocation and is validated against Patterson and Jones (2012),
Table II. Low-CV data return `NOT_EVALUABLE` for standard ABE routing; incomplete
or unbalanced data fail closed.

The dissolution workbench accepts typed vessel-level rows and delegates all
calculations to `openpkflow.dissolution.run_dissolution_workbench()`. It rejects
duplicates, non-finite values, and unmatched vessel/formulation time points.
The API adapter does not interpolate, reindex, or implement formulas.

## Deployment status

The production service is <https://openpkflow.onrender.com>. On 2026-07-30,
`/health` and `/openapi.json` reported engine version 2.8.0 from `main`.
Documentation-only merges also redeploy Render, so `/health.git_sha` is the
source of truth for the current deployed commit. The scheduled/manual
convergence check requires both versions plus the expected commit.

## Tests

```powershell
$env:PYTHONPATH='src;api'
python -m pytest api/tests -q
```
