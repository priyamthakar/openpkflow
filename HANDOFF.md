# Handoff -- start here

**Project:** OpenPKFlow
**Last updated:** 2026-07-09
**Current version in tree:** 2.6.0
**Primary branch for this work:** `feat/v2.6.0-improvement-sprint`
**Open PR:** https://github.com/priyamthakar/openpkflow/pull/27

---

## Latest handoff update -- 2026-07-09, v2.6.0 improvement sprint

This section supersedes older v2.3 / v2.4 notes for current takeover work.
Start every session with:

```powershell
git status --short --branch
git log --oneline -5
git fetch origin
```

Read **this file first**, then `AGENTS.md` (or `CLAUDE.md`) for scope rules.
When ROADMAP.md and AGENTS.md disagree, **AGENTS.md wins**.

### Where the code is

| Location | State |
|---|---|
| Branch `feat/v2.6.0-improvement-sprint` | Feature commit pushed: `b53112c` |
| PR #27 | Open against `main` -- merge when CI is green |
| `main` / `origin/main` | Still at pre-v2.6.0 tip (`cd9b4b0` docs logo) until PR merges |
| Tag `v2.6.0` | **Not created yet** |
| PyPI / GitHub Release for 2.6.0 | **Not published yet** |

Version files already say **2.6.0**:
- `pyproject.toml`
- `src/openpkflow/__init__.py`
- `CHANGELOG.md` and `docs/changelog.md` both have `## [2.6.0] -- 2026-07-09`

### What v2.6.0 shipped (in the PR)

**Library (`src/openpkflow/`)**
- `pipeline/` -- `PipelineConfig`, `StudyPipeline`, `StudyPipelineResult`, HTML/MD reports
- CLI: `openpkflow study run config.json --report out.html [--json out.json]`
- `dissolution/supac.py` -- `classify_supac_ir_level`, `alcohol_dose_dumping_assessment` (screening only)
- `ivivc/level_bc.py` -- MDT, MRT, Level B/C linear correlation helpers
- `sim/methods.py` -- `c_1cmt_oral_transit`, `steady_state_metrics_1cmt_oral`
- Template: `report/templates/pipeline_report.html`

**API / webapp**
- `POST /api/be/power`, `POST /api/be/sample-size` + BE page Power calculator tab
- Multi-media dissolution analyze/report + Dissolution page tab
- IVIVC load-example + dose_diss / dose_iv UI
- Playwright smoke tests extended in `webapp/tests/paste-run.spec.ts`

**Validation / docs**
- `tests/validation/test_ivivc_convolution_reference.py` (analytical + independent Riemann check)
- BE power edge cases in `tests/validation/test_be_power_reference.py`
- `docs/positioning.md`, `docs/tutorials/pipeline.md`
- Docker / docker-compose polish; `examples/pipeline_walkthrough.py`, `examples/study_pipeline_example.json`

### Verification already run (2026-07-09)

| Check | Result |
|---|---|
| Full pytest (ignore SAEM/bayes MCMC, `-k "not MCMC and not mcmc"`) | **1264 passed** |
| New library tests (pipeline, supac, level B/C, transit, SS, convolution, BE edges) | **79 passed** |
| API `tests/test_be.py` + `tests/test_dissolution.py` | **13 passed** |
| Pre-commit on commit `b53112c` | Passed (ruff, format, yaml/toml) |
| Pipeline smoke | `StudyPipeline` on example JSON writes report with disclaimer |

### Intentionally untracked (do not commit)

- `.wrangler/`
- `Untitled-handoff.zip`, `untitled-handoff-extracted/`
- `webapp/test-results/`

### Still open after PR merge (priority order)

1. **Merge PR #27** when GitHub Actions are green; fix CI if anything fails.
2. **Release v2.6.0** (see `RELEASE.md`):
   - `python scripts/release_readiness.py`
   - `python -m pytest -q` (and slow suite if required for this cut)
   - `mkdocs build --strict`
   - `python -m build && python -m twine check dist/*`
   - Tag `v2.6.0`, GitHub release notes from `docs/changelog.md`, PyPI, conda-forge sync
3. **Product follow-ups** (in scope, not blocking tag):
   - Webapp page for study pipeline (library/CLI already works)
   - API + pages for sparse NCA / MAP PK
   - SUPAC / alcohol UI on top of `dissolution.supac`
   - Hosted deploy of api + webapp (`VITE_API_URL`)
4. **Science / validation (lower priority, do not overclaim):**
   - Formal RSABE stays in **BioEqPy**, not here
   - Keep `pop/estimation/` **frozen** (bug fixes only)
   - Optional: wire IVIVC stage into `StudyPipeline` (needs multi-array inputs, not single CSV)

### Prompt for next agent

```text
You are taking over OpenPKFlow in D:\openpkflow.

1. Read HANDOFF.md (top section dated 2026-07-09) then AGENTS.md for scope.
2. git status / git log / check PR https://github.com/priyamthakar/openpkflow/pull/27
3. Current code version is 2.6.0 on branch feat/v2.6.0-improvement-sprint (commit b53112c).
4. Immediate goals (ask user which to prioritize if unclear):
   a) Get CI green and merge PR #27 into main
   b) Tag and release v2.6.0 using RELEASE.md (do not overclaim RSABE or Part 11)
   c) Next features: pipeline web page, sparse/MAP API pages, SUPAC UI, deploy
5. Never extend pop/estimation/ beyond bug fixes.
6. Never put pharmacometric math in api/ or webapp/ -- library first.
7. Never use --no-verify. Fix hooks instead.
8. Windows ASCII-only for CLI output and public docstrings.
```

---

## Architecture cheat sheet (post-v2.6.0)

### Module map (`src/openpkflow/`)

```
dissolution/   f1/f2, bootstrap, MSD, models, multi_media, supac (v2.6)
nca/           AUC, lambda_z, SS, urine, sparse, CDISC PP
ivivc/         Level A + level_bc (MDT/MRT/Level B-C helpers)
sim/           1/2-cmt analytical + transit oral + SS metrics (v2.6)
pipeline/      StudyPipeline orchestration (v2.6)  <-- NEW
be/            TOST, power/n, replicate screening (research-grade)
bayes/         MAP + optional PyMC
pop/           GOF/VPC + estimation/ FROZEN
report/        HTML/PDF/DOCX templates (includes pipeline_report.html)
student/       simplified teaching APIs
validation/    (package helpers; real tests live in tests/validation/)
cli.py         dissolution, be, ivivc, pop, study run
```

### Web layer

```
api/app/routers/   nca, dissolution (+ multi-media), sim, ivivc, be (+ power/sample-size)
webapp/src/pages/  Home, Nca, Dissolution (single + multi-media tab),
                   Sim, IvIvc, Be (analysis + power tab)
progress_web_app.md  <-- web-only next candidates
```

### Key commands

```powershell
pip install -e ".[dev]"

# Standard suite (exclude slow MCMC)
pytest --ignore=tests/pop/test_saem.py --ignore=tests/bayes/test_bayes_be.py -k "not MCMC and not mcmc"

# New v2.6 areas
pytest tests/pipeline/ tests/dissolution/test_supac.py tests/ivivc/test_level_bc.py tests/sim/test_transit.py tests/sim/test_steady_state_metrics.py tests/validation/test_ivivc_convolution_reference.py -q

# API
cd api; pytest tests/test_be.py tests/test_dissolution.py -q; cd ..

# Pipeline CLI
openpkflow study run examples/study_pipeline_example.json --report out.html

# Release gate
python scripts/release_readiness.py
python -m build
python -m twine check dist/*
```

### Pharmacometric rules (do not violate)

1. f1/f2 require matched time points; no silent reindex.
2. AUC method must be explicit.
3. CL_F vs CL naming discipline.
4. BLQ handling must be explicit.
5. AUClast stops at tlast (trailing zeros trimmed in study.py).
6. NaN/Inf rejected.
7. Disclaimer required in all generated reports.
8. Do not copy R package source.

---

## Cross-validation status (summary)

| Module | External cross-val | Status |
|--------|--------------------|--------|
| NCA single-dose | PKNCA + NonCompart + WinNonlin | Done |
| NCA steady-state / urine | PKNCA / independent R | Done |
| Dissolution f1/f2 / models / bootf2 point | R refs | Done |
| IVIVC WN + LR | Independent R algebraic | Done |
| IVIVC convolution + Levy | Analytical + independent Riemann (v2.6) | Done |
| BE TOST power/n | PowerTOST 1.5-7 | Done |
| BE replicate screening | Scalar fixtures only | Research-grade |
| Pop PK FOCE-I | nlme (within tol) | Done; engine frozen |
| SUPAC / alcohol helpers | Unit + guidance-cited tests | Screening only |

Full mapping: `VALIDATION.md`, `docs/validation-matrix.md`.

---

## Historical notes (do not prioritize)

Older sprint detail for v2.3 (FOCE-I nlme, covariate removal) and v2.4 (replicate BE screening, release_readiness) is in git history and `CHANGELOG.md`. Those releases are done; do not re-run their handoff prompts unless debugging a regression.

**v2.4.0** shipped research-grade replicate BE screening -- still not formal RSABE.
**v2.5.0** web app layer (`api/` + `webapp/`) and student helpers.
**v2.6.0** is the current unreleased (until tag) improvement sprint on PR #27.
