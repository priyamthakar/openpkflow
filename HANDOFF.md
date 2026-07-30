# OpenPKFlow Handoff

**Last updated:** 2026-07-30

## Current state

The latest public release is **v2.7.1**. The **v2.8.0 Advanced Dissolution
Workbench is an unreleased candidate** in:

- worktree: `D:\openpkflow-v2.8.0`
- branch: `release/v2.8.0`
- base: `origin/main` at `e49e3f9` (v2.7.1 publication-state documentation)

Do not describe v2.8.0 as published until the remaining local, PR/CI,
publication, fresh-install, and hosted-convergence gates below pass.

The original `D:\openpkflow` checkout and its user-owned untracked content
remain untouched.

## Public production state

OpenPKFlow v2.7.1 is published and hosted convergence is verified:

- Release PR: [#43](https://github.com/priyamthakar/openpkflow/pull/43),
  squash-merged as `d24263d`.
- GitHub Release:
  [v2.7.1](https://github.com/priyamthakar/openpkflow/releases/tag/v2.7.1).
- Trusted Publishing:
  [run 30334756702](https://github.com/priyamthakar/openpkflow/actions/runs/30334756702).
- PyPI: <https://pypi.org/project/openpkflow/2.7.1/>.
- Cloudflare frontend and GitHub Pages documentation return HTTP 200.
- Render `/health` and `/openapi.json` report v2.7.1 at branch `main`, commit
  `d24263dda6f0a094ad54bf1383d273a6623d796c`, service
  `srv-d8fb63navr4c73a3gclg`.
- Conda-forge staged-recipes PR
  [#33461](https://github.com/conda-forge/staged-recipes/pull/33461)
  remains green and awaits maintainer review for v2.7.0.

## v2.8.0 candidate scope

The candidate adds orchestration and product surfaces around already validated
dissolution calculations. It does not add a new pharmacometric formula.

### Core package

- `DissolutionWorkbenchConfig` preserves the exact point-f2 method, bootstrap
  replicate count, confidence level, seed, and model-comparison selection.
- `run_dissolution_workbench()` validates and normalizes vessel rows, then
  delegates to existing f1/f2, bootstrap f2, model fitting,
  model-dependent comparison, MSD, and maximum-deviation functions.
- Only the five independently cross-validated models are promoted:
  zero-order, first-order, Higuchi, Korsmeyer-Peppas, and Weibull.
- The workflow rejects non-finite values, duplicate vessel/time rows, empty
  vessel identifiers, fewer than two vessels, fewer than three time points,
  within-formulation time mismatch, and reference/test time mismatch.
- No interpolation or silent reindexing is performed.
- HTML, PDF, and DOCX reports include vessel/mean plots, normalized input,
  model rankings, warnings, exact configuration, and the required disclaimer.
- The deterministic-layout audit ZIP contains normalized CSV, configuration,
  serialized results, HTML report, and a SHA-256 manifest.

### API and web app

- Three typed endpoints raise the API inventory from 29 to 32:
  - `POST /api/dissolution/workbench/analyze`
  - `POST /api/dissolution/workbench/report`
  - `POST /api/dissolution/workbench/audit-bundle`
- `/dissolution` has an **Advanced workbench** tab with canonical CSV upload,
  editable vessel rows, reference/test mapping, bootstrap configuration,
  vessel/mean visualization, five-model ranking, alternative metrics, report
  downloads, and audit ZIP download.
- FastAPI and React remain adapters; calculations stay in
  `src/openpkflow/dissolution/`.

## Validation checkpoint

Completed on the candidate:

- mandatory pre-feature v2.7.1 wheel/sdist build and Twine check: passed
- focused core workbench tests: **11 passed**
- dissolution plus validation suites: **413 passed, 22 deselected**
- API suite: **59 passed**
- frontend lint and production build: passed
- Playwright: **21 passed**, including example, uploaded CSV, report, and audit
  workbench flows
- Ruff and format: passed
- strict mypy: **87 source files**, passed
- strict MkDocs build: passed
- full standard non-MCMC suite: **1,324 passed, 22 deselected**
- all-files pre-commit second pass: passed
- final v2.8.0 wheel/sdist and Twine check: passed
- fresh-wheel environment:
  - `openpkflow version` -> `openpkflow 2.8.0`
  - similarity CLI -> f1 `2.000`, f2 `92.47`
  - workbench configuration and runner imports: passed

Dependency re-check on 2026-07-30:

- npm still reports 7.18.1 as the latest `react-router-dom` release.
- `npm audit` flags GHSA-qwww-vcr4-c8h2 for React Router versions from 7.12.0
  through 8.2.0.
- The advisory states that only unstable RSC APIs are affected. OpenPKFlow is
  a client-only Vite SPA and uses neither RSC mode nor server actions.
- The advisory's patched 8.3.0 release is not available from npm. Do not apply
  npm's suggested forced downgrade; re-check before publication.

The first background full-suite attempt was intentionally discarded after a
release-order audit found `pyproject.toml` at 2.8.0 while
`openpkflow.__version__` was still 2.7.1 in that process. The source version is
now corrected; accept only a fresh full-suite run started after that fix.

## Remaining v2.8.0 gates

1. Commit the settled candidate, then run clean-tree
   `scripts/release_readiness.py`.
2. Push and open a normal pull request; require every CI check.
3. Squash-merge without force-push or bypassing hooks.
4. Tag the exact merged `main` commit as `v2.8.0`, create the GitHub Release,
   and require Trusted Publishing to TestPyPI and PyPI.
5. Verify a fresh public-index installation.
6. Require Cloudflare/docs health and Render `/health` plus `/openapi.json` to
   report v2.8.0 at the merged commit before claiming hosted convergence.

## Deployment

| Piece | URL | Verified public state |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | v2.7.1 surface, HTTP 200 |
| Backend | https://openpkflow.onrender.com | v2.7.1 at `d24263d` |
| Docs | https://priyamthakar.github.io/openpkflow/ | v2.7.1 docs, HTTP 200 |
| PyPI | https://pypi.org/project/openpkflow/2.7.1/ | public install verified |

## Constraints

- Do not extend `pop/estimation/`; bug fixes only.
- Do not add EMA ABEL, full-replicate RSABE, NTI decisions, or unvalidated
  formal BE designs.
- Preserve explicit AUC method and BLQ handling.
- Keep pharmacometric logic in `src/openpkflow/`, never in `api/` or `webapp/`.
- Do not use `--no-verify`, force-push, or amend published commits.
- Preserve the original checkout and continue release work in the isolated
  worktree.
