# OpenPKFlow Handoff

**Last updated:** 2026-07-16

## Current state

- Latest release: **v2.6.0**, published on 2026-07-15.
- Main post-release commit: `6087cd9` (`feat(pipeline): add web workflow and reproducibility audit bundle (#30)`).
- GitHub release: <https://github.com/priyamthakar/openpkflow/releases/tag/v2.6.0>
- PyPI: <https://pypi.org/project/openpkflow/2.6.0/>
- Working branch: `agent/sparse-nca-web`.
- Draft PR: <https://github.com/priyamthakar/openpkflow/pull/31>
- Pipeline API/page/audit bundle: merged in PR #30.
- Conda-forge staged-recipes PR #33461 targets v2.6.0 and passes the linter plus
  Linux, Windows, and macOS builds; it awaits maintainer review.
- Active post-release work: sparse NCA external validation, API/report endpoints,
  and React page are implemented on the working branch.
- Detailed session record: `SESSION_SUMMARY_2026-07-15.md`.

## v2.6.0 release verification

- Standard suite: 1275 passed, 22 deselected.
- Targeted affected suite: 291 passed.
- API suite: 27 passed before the post-release pipeline endpoints were added.
- Browser suite: 8 Playwright tests passed.
- Strict mypy: 80 non-frozen source files passed. Frozen `pop/estimation/` has an
  explicit configuration override and remains bug-fix only.
- Ruff, pre-commit, strict MkDocs, package build, and Twine checks passed.
- GitHub Actions main CI and tag publish workflows succeeded.
- Fresh install of `openpkflow==2.6.0` verified `openpkflow version` and
  `openpkflow similarity`.

## Pipeline slice: merged and verified

The branch adds an additive core/API slice without adding pharmacometric math to
the adapter layer.

- Core `StudyPipelineResult.audit_bundle()` writes a ZIP containing normalized
  inputs, `config.json`, `results.json`, `report.html`, and a SHA-256 manifest.
- FastAPI endpoints:
  - `POST /api/pipeline/analyze`
  - `POST /api/pipeline/report`
  - `POST /api/pipeline/audit-bundle`
- Pipeline schema, service, router registration, and API tests follow the existing
  adapter pattern.
- React `/pipeline` page supports one to three stage uploads, explicit dissolution,
  NCA/BLQ, and paired-BE options, unified stage results, report download, and audit
  ZIP download.
- Typed frontend contracts/API wrappers, route/sidebar registration, and mocked
  Playwright coverage are included.
- Verification on 2026-07-15:
  - `python -m pytest tests/pipeline -q` -> 12 passed
  - pipeline API tests -> 3 passed
  - full API suite -> 30 passed
  - targeted Ruff -> passed
  - targeted mypy -> passed (7 source files)
  - strict MkDocs build -> passed
- Verification on 2026-07-16 after the React page was added:
  - frontend ESLint -> passed
  - frontend production build -> passed
  - Playwright -> 9 passed
  - full API suite -> 30 passed
  - pipeline core suite -> 12 passed
  - targeted Ruff and strict mypy -> passed
  - standard Python suite -> 1276 passed, 22 deselected
  - package build and Twine checks -> passed

## Sparse NCA branch: implemented and verified

- Core input validation rejects non-finite values, negative values, non-increasing
  times, all-zero profiles, and non-positive doses before nonlinear fitting.
- Independent cross-validation matches R 4.6.0 `stats::nls` on five samples from
  published `nlme::Theoph` subject 1 for CL_F, Vz_F, ka, and fitted concentrations.
- Reproducible reference script: `scripts/sparse_nca_theoph_crossval.R`.
- Core HTML/Markdown screening reports include the required disclaimer and explicit
  model-informed/non-primary scope caveat.
- API endpoints: `POST /api/nca/sparse/analyze` and `/api/nca/sparse/report`.
- React `/nca/sparse` page provides a published Theoph example, paste grid, fit
  diagnostics, observed/fitted chart and table, and report downloads.
- Verification on 2026-07-16:
  - frontend ESLint and production build -> passed
  - Playwright -> 10 passed
  - full API suite -> 34 passed
  - NCA plus validation suites -> 517 passed, 22 deselected
  - targeted Ruff and strict mypy -> passed
  - standard Python suite -> 1285 passed, 22 deselected
  - package build and Twine checks -> passed

## Resume here

1. Review draft PR #31 and its CI results.
2. Address actionable review feedback, if any.
3. Mark ready and merge after review and required checks.
4. Await conda-forge maintainer action on PR #33461; do not recreate the recipe.
5. Only then begin the MAP individual-PK API/page slice.

Do not extend frozen `pop/estimation/`. Keep formal RSABE in BioEqPy. Validation
work outranks new modules.

## Future plan, in priority order

1. Review and merge the completed sparse NCA validation/API/page slice.
2. Await conda-forge maintainer review of the green v2.6.0 recipe in PR #33461.
3. Add MAP individual PK API/page, preserving screening-only positioning and
   fail-closed diagnostics.
4. Add SUPAC/alcohol screening UI with prominent scope caveats.
5. Deploy the API/static webapp and document `VITE_API_URL`, health checks,
   file-size limits, and rollback steps.

## Commands

```powershell
git status -sb
python -m pytest tests/pipeline -q
$env:PYTHONPATH='src;api'; python -m pytest api/tests -q --basetemp D:\openpkflow\.test-tmp
python -m ruff check src/openpkflow/pipeline api/app/routers/pipeline.py api/app/schemas/pipeline.py api/app/services/pipeline_service.py api/tests/test_pipeline.py tests/pipeline
python -m mypy src/openpkflow/pipeline api/app/routers/pipeline.py api/app/schemas/pipeline.py api/app/services/pipeline_service.py
```

Full release checks remain documented in `RELEASE.md`.

## Identity

**Package:** openpkflow

**Author:** Priyam Thakar <priyamthakar1@gmail.com>

**GitHub:** <https://github.com/priyamthakar/openpkflow>
**Positioning:** A transparent, reproducible, open-source Python workflow for
dissolution, NCA, PK/PD simulation, and pharmacometric reporting. It does not
replace expert regulatory judgement or validated commercial platforms.
