# Tutorial: Formulation-to-report pipeline

This tutorial shows the intended **sequential** study workflow with OpenPKFlow:
dissolution similarity, NCA on a PK dataset, then optional BE screening and
reports.

See also [Positioning](../positioning.md) for scope limits (not Part 11,
research-grade PopPK, RSABE in BioEqPy).

---

## 0. Install

```bash
pip install openpkflow
# Optional reports:
pip install "openpkflow[reports]"
```

---

## Unified study pipeline (recommended)

Run dissolution + NCA (+ optional BE) from one JSON config and get a single report:

```bash
openpkflow study run examples/study_pipeline_example.json --report out/study.html
openpkflow study run examples/study_pipeline_example.json --json out/study.json
```

Python:

```python
from openpkflow.pipeline import PipelineConfig, StudyPipeline

cfg = PipelineConfig(
    title="Demo study",
    dissolution_csv="path/to/dissolution.csv",
    dissolution_reference="reference",
    dissolution_test="test",
    nca_csv="path/to/nca.csv",
    nca_auc_method="linear_up_log_down",
    nca_blq_method="none",
)
result = StudyPipeline(cfg).run()
print(result.summary())
result.report("out/study.html")
result.audit_bundle("out/study-audit.zip")
```

AUC and BLQ methods must be explicit (never silent defaults). Stages without
inputs are skipped. Failures are not swallowed; see `result.metadata`.

The audit ZIP preserves copied inputs, normalized configuration, serialized results,
an HTML report, and a SHA-256/size manifest for reproducibility review.

### Web and API workflow

With the backend and frontend running, open `/pipeline`. Upload any combination of
dissolution, NCA, and paired-BE CSVs, configure the enabled stages, then download a
unified HTML/Markdown report or the audit ZIP.

Programmatic clients can call `/api/pipeline/analyze`, `/api/pipeline/report`, and
`/api/pipeline/audit-bundle`. The adapter only orchestrates public core APIs and does
not contain pharmacometric formulas.

The sections below show each stage in isolation (still useful for debugging).

---

## 1. Dissolution similarity (CLI)

CSV columns: `formulation`, `batch`, `time`, `percent_released`.

```bash
openpkflow dissolution compare data/dissolution.csv ^
  --reference reference --test test ^
  --report out/dissolution.html
```

On Unix shells use `\` line continuations instead of `^`.

Quick numeric check without a full study CSV:

```bash
openpkflow similarity --reference "20,40,60,80,90" --test "21,39,61,79,88"
```

**Interpretation (FDA 1997 IR dissolution guidance):** f2 >= 50 suggests
similarity; f1 < 15 is a complementary criterion sometimes used.

### Python equivalent

```python
from openpkflow.datasets import example_dissolution_path
from openpkflow.dissolution import DissolutionStudy

study = DissolutionStudy.from_csv(example_dissolution_path())
result = study.compare(reference="reference", test="test")
print(result.summary())
result.report("out/dissolution.html")
```

---

## 2. NCA (Python API)

There is no dedicated `openpkflow nca` CLI subcommand yet. Use the library API
with explicit AUC and BLQ methods (required).

```python
from openpkflow.datasets import example_theoph_path
from openpkflow.nca import NCAStudy

study = NCAStudy.from_csv(
    example_theoph_path(),
    auc_method="linear_up_log_down",
    blq_method="none",
)
summary = study.analyze()
print(summary.to_dataframe()[["subject", "Cmax", "AUClast", "half_life", "CL_F"]])
summary.report("out/nca_summary.html")
```

Built-in Theoph path: R `nlme::Theoph` 12-subject oral theophylline dataset.

---

## 3. Bioequivalence screening (CLI)

Wide CSV: one row per subject with `subject`, `reference`, `test`
(optional `sequence`).

```bash
openpkflow be compare be_params.csv --parameter AUCinf --report out/be.html
```

This is a **2x2 TOST convenience layer** for screening and teaching. Formal
replicate / RSABE work belongs in the companion BioEqPy package, not here.

### From NCA results (Python)

```python
from openpkflow.be import BEStudy

# After you have paired reference/test NCA parameters per subject:
# be = BEStudy.from_nca_results(...)  # see reference docs
# or load a wide CSV of AUCinf / Cmax pairs
```

Power and sample size (exact TOST, PowerTOST-aligned):

```python
from openpkflow.be.methods import be_tost_power, be_sample_size

print(be_tost_power(gmr=0.95, cv=0.20, n=24))
n, achieved = be_sample_size(gmr=0.95, cv=0.20, target_power=0.80)
print(n, achieved)
```

---

## 4. Optional IVIVC Level A

When developing extended-release formulations with IV UIR and oral profiles:

```python
from openpkflow.ivivc import IVIVCStudy  # see tutorials/ivivc.md

# Wagner-Nelson or Loo-Riegelman deconvolution, Levy plot, %PE predictability
```

Convolution prediction of plasma profiles from dissolution + UIR is documented
in the IVIVC tutorial and cross-checked in
`tests/validation/test_ivivc_convolution_reference.py`.

---

## 5. End-to-end example script

From the repository root (after `pip install -e .`):

```bash
python examples/pipeline_walkthrough.py
```

That script runs dissolution on the bundled example CSV and NCA on Theoph, then
prints ASCII summaries. It stays dependency-light (core package only).

---

## 6. Docker notes

**Library + Jupyter (root Dockerfile):**

```bash
docker compose up -d
# Jupyter Lab on http://localhost:8888
```

**API adapter (separate image):**

```bash
docker build -t openpkflow-api -f api/Dockerfile .
docker run --rm -p 8000:8000 openpkflow-api
```

**Web UI:** run the FastAPI backend, then `cd webapp && npm install && npm run dev`
(see `webapp/README.md`). Optional `api` / `webapp` services can be added to
`docker-compose.yml` for local stacks; the default compose file targets Jupyter.

---

## Disclaimer

All generated reports include:

> This report was generated using OpenPKFlow (open-source). Final regulatory
> interpretation should be reviewed by qualified formulation, pharmacokinetic,
> and regulatory experts.

OpenPKFlow does not replace expert judgement or commercial systems under
21 CFR Part 11 controlled environments.
