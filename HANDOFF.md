# OpenPKFlow Handoff

**Last updated:** 2026-07-15

## Current state

- Latest release: **v2.6.0**, published on 2026-07-15.
- Main release commit: `8a3298a` (`chore(release): harden v2.6.0 CI and API (#29)`).
- GitHub release: <https://github.com/priyamthakar/openpkflow/releases/tag/v2.6.0>
- PyPI: <https://pypi.org/project/openpkflow/2.6.0/>
- Working branch: `agent/pipeline-web-audit-bundle`.
- Draft PR: <https://github.com/priyamthakar/openpkflow/pull/30>
- Active post-release work: pipeline API plus downloadable audit bundle. The React
  pipeline page has not been started.
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

## Current branch: implemented and verified

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
- Verification on 2026-07-15:
  - `python -m pytest tests/pipeline -q` -> 12 passed
  - pipeline API tests -> 3 passed
  - full API suite -> 30 passed
  - targeted Ruff -> passed
  - targeted mypy -> passed (7 source files)
  - strict MkDocs build -> passed

## Resume here

1. Check out draft PR #30 / `agent/pipeline-web-audit-bundle`, then inspect
   `git status` before editing.
2. Build the React pipeline page using the new endpoints. Add typed API wrappers,
   result types, route/sidebar registration, report download, and audit-bundle
   download.
3. Add Playwright coverage with mocked pipeline responses, then run frontend lint,
   build, and browser tests.
4. Run the full API suite from `api/` or with `PYTHONPATH=src;api` from the repo root.
5. Run the standard Python suite and release build checks before merging.

Do not extend frozen `pop/estimation/`. Keep formal RSABE in BioEqPy. Validation
work outranks new modules.

## Future plan, in priority order

1. Finish and merge the pipeline web page plus audit-bundle flow.
2. Update conda-forge staged-recipes PR #33461 from 2.3.0 to 2.6.0 and refresh
   hashes; no feedstock/package exists yet.
3. Add sparse NCA API/page, with explicit AUC and BLQ methods.
4. Add MAP individual PK API/page, preserving screening-only positioning and
   fail-closed diagnostics.
5. Add SUPAC/alcohol screening UI with prominent scope caveats.
6. Deploy the API/static webapp and document `VITE_API_URL`, health checks,
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
