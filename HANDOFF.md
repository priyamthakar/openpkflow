# OpenPKFlow Handoff

**Last updated:** 2026-07-16

## Current state

- Latest release: **v2.6.0**, published on 2026-07-15.
- Main post-release commit: `6087cd9` (`feat(pipeline): add web workflow and reproducibility audit bundle (#30)`).
- GitHub release: <https://github.com/priyamthakar/openpkflow/releases/tag/v2.6.0>
- PyPI: <https://pypi.org/project/openpkflow/2.6.0/>
- Working branch: `agent/sparse-nca-web`.
- Draft PR: <https://github.com/priyamthakar/openpkflow/pull/31>
- Verified baseline: `bb5170c` (`docs(project): synchronize sparse and pipeline documentation`).
- At that baseline, PR #31 is mergeable. Python 3.10/3.11/3.12, API, frontend, Python 3.13
  Linux/Windows smoke, type check, pre-commit, and Cloudflare Workers preview checks
  are green. There are no reviews or actionable comments as of this update.
- Pipeline API/page/audit bundle: merged in PR #30.
- Conda-forge staged-recipes PR #33461 targets v2.6.0 and passes the linter plus
  Linux, Windows, and macOS builds; it awaits maintainer review.
- Active post-release work: sparse NCA external validation, reports, API endpoints,
  React page, and synchronized user/developer documentation are complete on the
  working branch and awaiting review/merge.
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
  - strict MkDocs build and repository-wide pre-commit -> passed
  - GitHub CI and Cloudflare Workers branch preview -> passed at `bb5170c`

## Sparse NCA change map

- Core fit and reports: `src/openpkflow/nca/sparse.py`,
  `src/openpkflow/nca/reporting.py`.
- Independent reference: `scripts/sparse_nca_theoph_crossval.R`,
  `tests/validation/test_sparse_nca_theoph_reference.py`.
- Core regression tests: `tests/nca/test_sparse_nca.py`.
- API adapter: `api/app/schemas/nca.py`, `api/app/services/nca_service.py`,
  `api/app/routers/nca.py`, `api/tests/test_nca.py`.
- React workflow: `webapp/src/pages/SparseNcaPage.tsx`, route/sidebar registration,
  typed API contracts, and `webapp/tests/paste-run.spec.ts`.
- User docs: `docs/tutorials/sparse-nca.md`, NCA reference/theory/validation pages,
  API/web READMEs, changelogs, positioning, roadmap, and migration guide.

## Resume here

1. Confirm the checkout is `agent/sparse-nca-web`, contains verified baseline
   `bb5170c`, and has a clean tree.
2. Review PR #31. CI is already green and there is currently no review feedback.
3. Mark ready and merge only after the required human/scientific review.
4. Await conda-forge maintainer action on PR #33461; do not recreate the recipe.
5. After merge, update local `main` and only then begin the MAP individual-PK
   API/page slice.

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
git log -1 --oneline
gh pr view 31
gh pr checks 31
python -m pytest tests/nca/test_sparse_nca.py tests/validation/test_sparse_nca_theoph_reference.py -q
$env:PYTHONPATH='src;api'; python -m pytest api/tests -q --basetemp D:\openpkflow\.test-tmp
python -m mkdocs build --strict --site-dir D:\openpkflow\.mkdocs-tmp
python -m pre_commit run --all-files
cd webapp
npm run lint
npm run build
npm run test:e2e
```

Full release checks remain documented in `RELEASE.md`.

## Identity

**Package:** openpkflow

**Author:** Priyam Thakar <priyamthakar1@gmail.com>

**GitHub:** <https://github.com/priyamthakar/openpkflow>
**Positioning:** A transparent, reproducible, open-source Python workflow for
dissolution, NCA, PK/PD simulation, and pharmacometric reporting. It does not
replace expert regulatory judgement or validated commercial platforms.
