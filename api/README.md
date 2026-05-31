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
| POST | `/api/dissolution/formulations` | List formulation labels from CSV |
| POST | `/api/dissolution/compare` | f1/f2 comparison |
| POST | `/api/dissolution/report` | Download dissolution report |
| POST | `/api/sim/simulate` | Run PK simulation (JSON body) |
| POST | `/api/sim/report` | Download sim report |

## Tests

```bash
cd api
pytest tests/ -q
```
