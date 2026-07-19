# OpenPKFlow Handoff

**Last updated:** 2026-07-19

## Current state

- Latest release: **v2.6.0**, published on 2026-07-15.
- PR #31 (sparse NCA) **merged** to `main` as squash commit `74c070b` on 2026-07-16.
  It is no longer pending review; the local `agent/sparse-nca-web` commits it was
  opened from are now superseded.
- Working branch: **`agent/map-supac-web`**, rebased onto `origin/main` (`74c070b`).
  The pre-session tip of this branch (`adcf052`) had a tree byte-identical to
  `74c070b` (verified via `git diff --quiet`), so the rebase (`git rebase --onto
  origin/main adcf052 agent/map-supac-web`) dropped the four now-redundant
  sparse-NCA-era commits with zero conflicts, keeping only this session's new work.
- All session changes (formal BE ANOVA, RSABE gate, MAP PK hardening, SUPAC/alcohol
  hardening) are committed, re-verified post-rebase, and open as
  [PR #32](https://github.com/priyamthakar/openpkflow/pull/32) against `main` (CI running).
- Conda-forge staged-recipes PR #33461 targets v2.6.0 and passes all platform builds; awaits maintainer review.
- Full non-MCMC suite run this session: 1302 passed, 1 pre-existing unrelated failure
  (`tests/nca/test_methods_hypothesis.py::TestAUCLinearInvariants::test_scale_invariance`,
  a Hypothesis-found float-underflow edge case at a subnormal double; `nca/` was not
  touched this session).

## What was done this session (agent/map-supac-web)

### New features

**Formal complete balanced TR/RT 2x2 crossover ANOVA** (`src/openpkflow/be/formal.py`)
- Full ANOVA source table with correct sequence denominator (subject-within-sequence)
- GMR, 90% CI, residual MSE, intra-subject CV, PASS/FAIL decision
- Fail-closed for: missing columns, NaN/Inf, non-positive values, missing sequences, duplicate periods, incomplete subjects, unbalanced allocation, misaligned treatment/period/sequence, fewer than 4 subjects
- Pinned independent R cross-check: `treatment_difference=0.095931482001`, `residual_mse=0.000183925324`, `sequence_f_subject_within_sequence=2.447340272021`

**FDA partial-replicate RSABE gate** (`src/openpkflow/be/rsabe.py`)
- Always returns `NOT_EVALUABLE` with `EXTERNAL_REFERENCE_REQUIRED`
- Validates TRR/RTR/RRT sequence presence only
- Must not be promoted to PASS/FAIL without a pinned external observed-data comparator

**Formal ANOVA reporting** (`src/openpkflow/be/formal_reporting.py`)
- HTML + Markdown reports with ANOVA table, treatment contrast, required disclaimer

**CLI: `openpkflow be anova`** — runs formal ANOVA from CSV with configurable column names

**API endpoints** (all registered in `api/app/main.py`):
- `POST /api/be/anova/analyze` returns `FormalBeResponse` (parameter, design, GMR, CI, ANOVA table, decision)
- `POST /api/be/anova/report` streams HTML/Markdown report download
- `POST /api/bayes/map/analyze` returns `MapPkResponse` (CL_F/Vz_F/ka, CL/Vz, diagnostics, fail-closed fit_usable flag)
- `POST /api/bayes/map/report` streams MAP screening report
- `POST /api/supac/classify` returns SUPAC-IR level with rationale and recommended tests
- `POST /api/supac/alcohol` returns f2 per ethanol concentration, overall pass/fail

**Frontend pages** (React + Vite + Tailwind, all lazy-loaded):
- `/be/anova` — Formal BE ANOVA page: file upload, metric cards (GMR, CI, CV, MSE), ANOVA table, report download
- `/bayes/map` — MAP Individual PK: Theoph example, paste grid, study details (route, dose, subject), fit diagnostics, observed/predicted chart + table, fail-closed suppression of unusable estimates
- `/supac` — SUPAC & Alcohol Screening: tabbed UI (SUPAC-IR level classifier + Alcohol dose-dumping), paste grids for control/ethanol profiles, f2 results by ethanol percentage

### Fixes and hardening

**MAP individual PK** (`src/openpkflow/bayes/map_pk.py`):
- Added fail-closed input validation: non-finite values, negative times/concentrations, non-increasing times, all-zero profiles, 1D array requirement, dose finite check
- Oral Cmax/Tmax changed from numerical grid search to analytical formula: Tmax = ln(ka/k) / (ka - k), with degenerate case when ka==k
- Ill-conditioned Hessian now returns `uncertainty_reliable=False` with no Hessian inverse instead of returning unreliable SEs

**MAP PK reports** (`src/openpkflow/bayes/reporting.py`):
- Jinja2 `autoescape` enabled for XSS prevention
- Test verifying `<script>` is escaped in subject name output

**SUPAC alcohol screening** (`src/openpkflow/dissolution/supac.py`):
- Added strict validation: finite time points, non-negative, strictly increasing, finite ethanol percentages in (0, 100]
- Changed from default f2 method to explicit `method="regulatory"` (trims extra plateau points per FDA guidance)
- f2 threshold must be finite and within (0, 100]

### Tests

**Core BE formal ANOVA** (`tests/be/test_formal.py`): 9 tests
- Identical profiles -> GMR=1, PASS, CV=0
- Treatment contrast matches expected
- Sequence uses subject-within-sequence F denominator
- 4 fail-closed parameterized cases (missing row, single sequence, duplicate, negative value)
- Unbalanced sequence allocation fails closed
- Report includes ANOVA Table

**RSABE gate** (`tests/be/test_rsabe_gate.py`): 1 test

**External reference** (`tests/validation/test_be_anova_reference.py`): 1 test
- Pinned against `scripts/be_anova_crossval.R` output

**MAP PK core** (`tests/bayes/test_map_pk.py`): 4 parameterized validation tests + report escaping test

**SUPAC core** (`tests/dissolution/test_supac.py`): 2 new validation tests + regulatory f2 trimming test

**API tests**:
- `api/tests/test_bayes.py`: 6 tests (oral MAP, IV MAP, too-few-samples, invalid profile, HTML report, HTML escaping)
- `api/tests/test_supac.py`: 6 tests (filler L1/L3, negative reject, alcohol divergence/pass, mismatched lengths, duplicate ethanol%)
- `api/tests/test_be.py`: 2 new formal BE tests (anova/analyze + anova/report), 113 total

**Playwright** (`webapp/tests/paste-run.spec.ts`):
- MAP happy path: submits oral profile, renders CL/F, renders metrics
- MAP unusable: fit_usable=false suppresses estimates and download button
- Alcohol screening: tab switch, sends control grid, renders fail verdict
- Formal BE ANOVA: file upload, renders ANOVA result table and GMR

## Change map (new files)

```
src/openpkflow/be/
  formal.py              -> FormalBEResult, formal_be_anova, AnovaRow
  formal_reporting.py    -> report_formal_be (HTML/Markdown)
  rsabe.py               -> FdaRsabeResult, fda_partial_replicate_rsabe
  __init__.py            -> exports new public symbols

scripts/
  be_anova_crossval.R    -> independent R ANOVA reference script

tests/be/
  test_formal.py         -> 9 formal ANOVA tests
  test_rsabe_gate.py     -> RSABE gate test

tests/validation/
  test_be_anova_reference.py   -> pinned regression vs R
  data/be_anova_balanced_2x2.csv -> R cross-check fixture (4 subjects)

api/app/routers/
  bayes.py               -> /api/bayes/map/analyze, /api/bayes/map/report
  supac.py               -> /api/supac/classify, /api/supac/alcohol

api/app/schemas/
  bayes.py               -> MapPkRequest, MapPkResponse
  supac.py               -> SupacClassifyRequest/Response, AlcoholDosingRequest/Response

api/app/services/
  bayes_service.py       -> run_map_pk, write_map_pk_report
  supac_service.py       -> run_supac_classify, run_alcohol_dosing

api/tests/
  test_bayes.py          -> 6 MAP PK endpoint tests
  test_supac.py          -> 6 SUPAC endpoint tests

webapp/src/pages/
  FormalBePage.tsx       -> /be/anova
  MapPkPage.tsx          -> /bayes/map
  SupacPage.tsx          -> /supac

docs/decisions/
  formal-be.md           -> architecture decision record
```

### Change map (modified files)

- `src/openpkflow/cli.py` — added `openpkflow be anova` command
- `src/openpkflow/bayes/map_pk.py` — enhanced validation, analytical Cmax/Tmax, ill-conditioned Hessian handling
- `src/openpkflow/bayes/reporting.py` — Jinja2 autoescape
- `src/openpkflow/dissolution/supac.py` — strict input validation, regulatory f2 method
- `src/openpkflow/be/__init__.py` — new public exports
- `api/app/main.py` — registered bayes and supac routers
- `api/app/routers/be.py` — added /anova/analyze and /anova/report endpoints
- `api/app/schemas/be.py` — FormalBeOptions, FormalBeResponse, FormalAnovaRow
- `api/app/services/be_service.py` — run_formal_be, write_formal_be_report
- `api/tests/test_be.py` — 2 new formal BE test cases
- `webapp/src/App.tsx` — lazy-loaded routes for /be/anova, /bayes/map, /supac
- `webapp/src/components/layout/Sidebar.tsx` — nav entries for all 3 new pages
- `webapp/src/lib/api.ts` — analyzeFormalBe, downloadFormalBeReport, analyzeMapPk, downloadMapPkReport, classifySupac, assessAlcoholDosing
- `webapp/src/lib/types.ts` — FormalBeResponse, FormalBeAnovaRow, MapPkRequest/Response, SupacClassify, AlcoholDosing types
- `webapp/tests/paste-run.spec.ts` — 4 new Playwright tests
- `tests/bayes/test_map_pk.py` — 4 validation tests + escaping test
- `tests/dissolution/test_supac.py` — 2 validation tests + regulatory f2 test
- `CHANGELOG.md`, `README.md`, `RELEASE.md`, `ROADMAP.md`, `CLAUDE.md`, `AGENTS.md` — synced
- Various docs: `docs/index.md`, `docs/positioning.md`, `docs/migration-cheatsheet.md`, `docs/reference/be.md`, `docs/tutorials/be.md`, `docs/validation-matrix.md`, `mkdocs.yml`, `api/README.md`, `webapp/README.md`

## Known issues / blocked items

1. **FDA partial-replicate RSABE** remains `NOT_EVALUABLE`. Cannot promote to PASS/FAIL until a pinned external observed-data comparator validates model fitting, sWR, upper confidence bound, point-estimate constraint, fallback behavior, and final decision for TRR/RTR/RRT data. See `docs/decisions/rsabe-validation-search.md` for the current dataset search: the leading candidate is `replicateBE::rds07` (public-domain, Schutz et al. 2020 AAPS J 22:44) cross-checked against a Pumas.ai FDA-style worked example on what appears to be the same dataset (`SLTGSF2020_DS07`) — not yet confirmed or wired into a test.

2. **PR #32** (formal BE ANOVA, RSABE gate, MAP PK, SUPAC/alcohol hardening) is open against `main` and awaits review/CI/merge.

3. **Conda-forge PR #33461** still awaits maintainer review.

## Resume here

1. PR #32 is open against `main`. Once merged, update this section and delete the resolved item above.
2. Await conda-forge maintainer action on PR #33461.
3. RSABE: pursue the `replicateBE::rds07` / Pumas `SLTGSF2020_DS07` lead in `docs/decisions/rsabe-validation-search.md` — confirm the dataset identity, reproduce CVwR and Howe's approximate statistic, and pin as a fixture if they match.
4. Deploy the API/static webapp once the PR above merges and conda-forge clears.
5. Do not extend frozen `pop/estimation/`.

## Commands

```powershell
# Current branch
git status -sb

# Verify baseline
git log -1 --oneline

# Core be tests
python -m pytest tests/be/ tests/validation/test_be_anova_reference.py -q

# MAP PK + SUPAC tests
python -m pytest tests/bayes/test_map_pk.py tests/dissolution/test_supac.py -q

# API tests
$env:PYTHONPATH='src;api'; python -m pytest api/tests -q --basetemp D:\openpkflow\.test-tmp

# Playwright tests
cd webapp && npm run test:e2e

# Full suite (exclude slow MCMC)
pytest --ignore=tests/pop/test_saem.py --ignore=tests/bayes/test_bayes_be.py -k "not MCMC and not mcmc"

# Lint and type-check
ruff check src/ tests/ api/ && ruff format --check src/ tests/ api/
mypy src/openpkflow

# Build
python -m build && python -m twine check dist/*
```

Full release checks remain documented in `RELEASE.md`.

## Identity

**Package:** openpkflow
**Author:** Priyam Thakar <priyamthakar1@gmail.com>
**GitHub:** https://github.com/priyamthakar/openpkflow
**Positioning:** A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting. It does not replace expert regulatory judgement or validated commercial platforms.
