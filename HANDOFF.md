# OpenPKFlow Handoff

**Last updated:** 2026-07-28

## Current state

OpenPKFlow **v2.7.1 is published and hosted convergence is verified**.

- Release PR: [#43](https://github.com/priyamthakar/openpkflow/pull/43),
  squash-merged to `main` as `d24263d`.
- Tag and GitHub Release:
  [v2.7.1](https://github.com/priyamthakar/openpkflow/releases/tag/v2.7.1).
- Trusted Publishing:
  [run 30334756702](https://github.com/priyamthakar/openpkflow/actions/runs/30334756702)
  completed successfully for TestPyPI and PyPI.
- PyPI: <https://pypi.org/project/openpkflow/2.7.1/>.
- A fresh public-index install reports `openpkflow 2.7.1`; the similarity CLI
  returns f1 `2.000` and f2 `92.47`.
- Frontend and documentation return HTTP 200.
- Render `/health` and `/openapi.json` report engine version 2.7.1.
- Render health provenance identifies:
  - branch `main`
  - commit `d24263dda6f0a094ad54bf1383d273a6623d796c`
  - service `srv-d8fb63navr4c73a3gclg`
- Conda-forge staged-recipes PR
  [#33461](https://github.com/conda-forge/staged-recipes/pull/33461)
  remains green and awaits maintainer review for v2.7.0.

## What v2.7.1 shipped

No pharmacometric calculation or public Python analysis API changed.

- `/health` reports non-secret deployment provenance: `git_sha`,
  `git_branch`, and `service_id`.
- `openpkflow.validation.deployment` provides a reusable fail-closed
  health/OpenAPI convergence verifier.
- `scripts/production_smoke.py` is the thin operations CLI wrapper.
- `.github/workflows/production-smoke.yml` runs the check manually or daily.
- Focused Playwright regressions cover:
  - PKChart legend hide and restore
  - PNG export
  - persisted desktop sidebar collapse
  - mobile navigation
- Shared `EmptyResults` placeholders are used across the remaining analysis
  result panes.
- FastAPI deployment requirement is updated to 0.140.

## Verification evidence

- local standard non-MCMC suite: **1,313 passed, 22 deselected**
- API suite: **55 passed**
- Playwright: **19 passed**
- Ruff, format, mypy (84 source files), pre-commit: passed
- strict MkDocs build: passed
- wheel/sdist and Twine checks: passed
- fresh local-wheel CLI smoke: passed
- PR CI:
  - Python 3.10, 3.11, and 3.12: passed
  - Linux and Windows Python 3.13 smoke: passed
  - API, frontend, type check, pre-commit: passed
  - Cloudflare build: passed
- tag-on-main verification and Trusted Publishing: passed
- fresh public-PyPI installation and CLI smoke: passed
- hosted Render version and commit convergence: passed

The first PR CI run exposed a Linux-only import-path defect in the production
smoke test. The reusable verifier was moved from the repository-root `scripts`
directory into the installed `openpkflow.validation` package; the exact CI API
invocation and subsequent full matrix passed.

The npm audit still reports a React Router advisory limited to unstable
RSC/server-action APIs. OpenPKFlow is a client-only Vite SPA and does not use
that path. At release time, npm still published 7.18.1 as latest and the patched
8.3.0 named by the advisory was unavailable. Do not force a breaking downgrade;
re-check the registry in the next release.

## Active next milestone: v2.8.0

The next worktree is:

- path: `D:\openpkflow-v2.8.0`
- branch: `release/v2.8.0`
- base: verified v2.7.1 release commit `d24263d` plus this documentation sync
  once merged

Implement the **Advanced Dissolution Workbench** by orchestrating already
validated core capabilities:

1. Vessel-level input, normalized tables, and profile plots.
2. Standard f1/f2 with bootstrap f2 confidence interval.
3. Five-model fitting with AICc ranking and diagnostics.
4. Model-dependent comparison.
5. MSD and maximum-deviation alternatives.
6. HTML/PDF/DOCX reports.
7. Reproducibility ZIP with normalized input, configuration, serialized
   results, report, and SHA-256 manifest.
8. Core orchestration/result API, FastAPI schemas/service/router, typed React
   workflow, API tests, Playwright tests, documentation, and release evidence.

## v2.8.0 gates

- Use existing validated functions in `src/openpkflow/dissolution/`; do not
  reimplement formulas in the API or frontend.
- Map every claim-bearing output to an existing validation fixture or add an
  independent published-reference test first.
- Fail closed on unmatched time points, invalid vessel data, non-finite values,
  or unsupported comparison conditions.
- Never silently interpolate or reindex f1/f2 inputs.
- Reports must include the required regulatory-review disclaimer and exact
  configuration.
- Complete package/API/web/docs/build validation before PR and publication.
- Verify PR/CI, tag, Trusted Publishing, fresh public install, and hosted
  version/commit convergence before claiming v2.8.0 complete.

## Deployment

| Piece | URL | Verified state |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | HTTP 200 after v2.7.1 merge |
| Backend | https://openpkflow.onrender.com | v2.7.1 at `d24263d` |
| Docs | https://priyamthakar.github.io/openpkflow/ | HTTP 200; deployment workflow passed |
| PyPI | https://pypi.org/project/openpkflow/2.7.1/ | public install verified |

## Resume here

1. Merge this v2.7.1 publication-state documentation sync.
2. Fast-forward `release/v2.8.0` to updated `origin/main`.
3. Re-run the mandatory clean distribution gate.
4. Implement the Advanced Dissolution Workbench in the order described in
   `ROADMAP.md`.
5. Preserve the validation and scope boundaries below.

## Constraints

- Do not extend `pop/estimation/`; bug fixes only.
- Do not add EMA ABEL, full-replicate RSABE, NTI decisions, or unvalidated
  formal BE designs.
- Preserve explicit AUC method and BLQ handling.
- Keep pharmacometric logic in `src/openpkflow/`, never in `api/` or `webapp/`.
- Do not use `--no-verify`, force-push, or amend published commits.
- Continue isolating release work from the original checkout and its
  user-owned untracked content.
