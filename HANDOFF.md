# OpenPKFlow Handoff

**Last updated:** 2026-07-28

## Read this first

The latest public release is still **v2.7.0**. A **v2.7.1 reliability release
candidate** is implemented but not fully validated, committed, pushed, merged,
tagged, published, or deployed. Do not describe v2.7.1 as released until every
gate in "Resume here" is complete and verified against public artifacts.

Release work is isolated in:

- worktree: `D:\openpkflow-v2.7.1-v2.8.0`
- branch: `release/v2.7.1`
- base: `origin/main` at `c14ac2e` plus local documentation commit `fea6319`

The original `D:\openpkflow` checkout and its user-owned untracked file remain
untouched.

## Public state

- GitHub and PyPI latest release: **v2.7.0** (2026-07-25).
- Release PR: [#39](https://github.com/priyamthakar/openpkflow/pull/39), squash
  merged as `74039b4`.
- Trusted Publishing:
  [run 30167426746](https://github.com/priyamthakar/openpkflow/actions/runs/30167426746).
- FastAPI dependency PR
  [#42](https://github.com/priyamthakar/openpkflow/pull/42) was squash-merged to
  `main` as `c14ac2e`; its checks were green.
- Conda-forge staged-recipes PR
  [#33461](https://github.com/conda-forge/staged-recipes/pull/33461) still
  targets v2.7.0, is green, and awaits maintainer review.
- Live verification on 2026-07-28:
  - Cloudflare frontend and documentation remain the published surfaces.
  - Render `/openapi.json` still reports engine version 2.6.0.
  - Render convergence is therefore open; do not claim a current backend
    deployment until both `/health` and `/openapi.json` match the expected
    release.

## v2.7.1 candidate scope

No pharmacometric formula or public Python analysis API is changed.

- `/health` adds non-secret deployment provenance:
  `git_sha`, `git_branch`, and `service_id`.
- `scripts/production_smoke.py` verifies deployed health status, package
  version, OpenAPI version, and optionally a Git commit prefix.
- `.github/workflows/production-smoke.yml` runs that convergence check on a
  schedule or manually.
- Focused Playwright tests cover:
  - PKChart legend hide and restore
  - PNG export
  - persisted desktop sidebar collapse
  - mobile drawer navigation and closure
- The shared `EmptyResults` component is now used across the remaining
  analysis result panes.
- Package metadata and both changelogs are assigned to 2.7.1.

## Verification checkpoint

Completed in the isolated worktree:

- mandatory pre-feature distribution gate: build succeeded and Twine checks
  passed for the clean v2.7.0 baseline
- Ruff lint: passed
- Ruff format check: passed after formatting three touched Python files
- mypy: **84 source files**, clean
- API suite: **55 passed**, with the existing sparse-fit covariance warning
- full standard non-MCMC suite: **1,313 passed, 22 deselected**
- frontend: ESLint clean, TypeScript/Vite build clean
- Playwright: **19 passed**, including the four new UI regressions
- strict MkDocs build: passed
- pre-commit: all hooks passed
- final v2.7.1 wheel/sdist: built and passed Twine checks
- fresh-wheel CLI smoke:
  - `openpkflow version` -> `openpkflow 2.7.1`
  - similarity -> f1 `2.000`, f2 `92.47`

Not yet completed:

- clean-tree `scripts/release_readiness.py`
- commit, push, PR, CI, merge, tag, GitHub Release, TestPyPI/PyPI
- fresh public-PyPI install and CLI smoke
- Render deployment and automated convergence verification

The npm audit reports the current React Router RSC advisory. OpenPKFlow is a
client-only Vite SPA and does not use the affected unstable RSC/server-action
path. The patched `react-router-dom` version named by the advisory was not
available from npm at this checkpoint. Do not use a forced downgrade or
`npm audit fix --force`; re-check the registry before release.

## v2.8.0 committed next milestone

After v2.7.1 is public and converged, implement the **Advanced Dissolution
Workbench** by exposing already validated core capabilities rather than adding
new pharmacometric algorithms:

1. Bootstrap f2 confidence intervals and decision summary.
2. Five-model dissolution fitting with AICc ranking and parameter diagnostics.
3. Model-dependent profile comparison.
4. MSD and maximum-deviation alternative comparisons.
5. Vessel-level profile tables and plots.
6. HTML/PDF/DOCX reports plus a reproducibility audit ZIP with normalized
   inputs, configuration, results, and SHA-256 manifest.
7. FastAPI schemas/service/router registration, typed React workflow, API tests,
   Playwright tests, documentation, and release validation.

Core calculations must remain in `src/openpkflow/dissolution/`. API and web code
are adapters only. Existing validation fixtures are the authority; any new
claim-bearing output requires an independent published-reference test before
exposure.

## Deployment

| Piece | URL | Current gate |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | auto-deploys from `main`; verify after merge |
| Backend | https://openpkflow.onrender.com | manual inspection/redeploy required; health and OpenAPI must converge |
| Docs | https://priyamthakar.github.io/openpkflow/ | docs workflow; verify after merge |
| PyPI | https://pypi.org/project/openpkflow/ | tag-triggered Trusted Publishing |

`webapp/.env.production` supplies the Render API URL. `render.yaml` supplies
CORS and service build/start configuration. Render injects commit/branch/service
metadata used by the enriched health response.

## Resume here

From `D:\openpkflow-v2.7.1-v2.8.0`:

1. Read the `github:yeet` skill, then commit, push, open the v2.7.1 PR, and wait
   for green CI before merge.
2. Run `python scripts/release_readiness.py` on the clean committed tree; only
   missing tag/release warnings are expected before publication.
3. Tag merged `main`, monitor Trusted Publishing, verify a fresh public-PyPI
   install, and run the CLI smoke checks.
4. Inspect or manually redeploy Render; run `scripts/production_smoke.py`
   against the expected version and commit.
5. Synchronize this handoff and the living docs to the verified public state.
6. Only then create the v2.8.0 branch and begin the Advanced Dissolution
   Workbench.

## Constraints

- Do not extend `pop/estimation/`; bug fixes only.
- Do not add EMA ABEL, full-replicate RSABE, NTI decisions, or unvalidated
  formal BE designs.
- Preserve explicit AUC method and BLQ handling.
- Keep pharmacometric logic in `src/openpkflow/`, never in `api/` or `webapp/`.
- Do not use `--no-verify`, force-push, or amend published commits.
- Preserve user-owned dirty/untracked content by continuing in the isolated
  worktree.
