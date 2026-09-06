# OpenPKFlow Handoff

**Last updated:** 2026-09-06

## Repo consolidation (2026-09-06)

Development is consolidated on `main`; the repo now uses a single-branch
workflow (`gh-pages` remains as the CI-managed docs deployment branch).

- Merged PR [#57](https://github.com/priyamthakar/openpkflow/pull/57)
  (uvicorn >=0.52.4) and PR [#58](https://github.com/priyamthakar/openpkflow/pull/58)
  (Playwright chrome-behavior coverage) into `main`.
- Fixed the long-broken `pre-commit` CI job: bumped `mirrors-mypy` to
  v1.20.2 (mypy 1.13 cannot parse numpy 2.3+ PEP 695 stubs) and capped the
  hook env at `numpy<2.5`, mirroring the CI Type check job.
- Landed the pending portfolio-demo availability doc polish from the
  `D:\openpkflow-docs-demo` worktree.
- Deleted all merged or superseded branches (local and remote): `release/*`,
  `docs/*` (except `gh-pages`), `fix/*`, `agent/*`, `pr52`, `test/*`, and the
  `subagent-*` scratch branches.
- Removed all secondary worktrees (`D:\openpkflow-v2.8.0`,
  `D:\openpkflow-docs-demo`, `D:\openpkflow-v2.7.0-release`,
  `D:\openpkflow-v2.7.1-docsync`, `D:\openpkflow-v2.7.1-v2.8.0`, and the
  agent scratch worktrees). The `D:\openpkflow` checkout remains the single
  working copy.

## Current state

OpenPKFlow **v2.8.0 is published and hosted convergence is verified**.

- Release PR: [#45](https://github.com/priyamthakar/openpkflow/pull/45)
- Squash-merge commit: `06338340be90b5a5dec4e70ebe2311f540d3b1b3`
- GitHub Release:
  [v2.8.0](https://github.com/priyamthakar/openpkflow/releases/tag/v2.8.0)
- Trusted Publishing:
  [run 30509130768](https://github.com/priyamthakar/openpkflow/actions/runs/30509130768)
- PyPI: <https://pypi.org/project/openpkflow/2.8.0/>
- Post-release documentation PRs:
  [#46](https://github.com/priyamthakar/openpkflow/pull/46) (`3923aff`) and
  [#47](https://github.com/priyamthakar/openpkflow/pull/47) (`4039ed8`)

The original `D:\openpkflow` checkout and its user-owned untracked content
remain untouched.

## v2.8.0 scope

The Advanced Dissolution Workbench turns already validated calculations into
one report-first, auditable workflow. It does not add a new pharmacometric
formula.

### Core package

- `DissolutionWorkbenchConfig` preserves the exact point-f2 method, bootstrap
  replicate count, confidence level, seed, and model-comparison selection.
- `run_dissolution_workbench()` validates vessel rows, then delegates to the
  existing f1/f2, bootstrap f2, model fitting, model-dependent comparison, MSD,
  and maximum-deviation implementations.
- Only five independently cross-validated models are promoted: zero-order,
  first-order, Higuchi, Korsmeyer-Peppas, and Weibull.
- Non-finite values, duplicate vessel/time rows, empty vessel identifiers,
  insufficient vessels/time points, and unmatched time grids fail closed.
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

## Verification evidence

Local release validation:

- focused core workbench tests: **11 passed**
- dissolution plus validation suites: **413 passed, 22 deselected**
- API suite: **59 passed**
- Playwright: **21 passed**
- full standard non-MCMC suite: **1,324 passed, 22 deselected**
- Ruff, format, strict mypy (87 source files), pre-commit, frontend lint/build,
  strict MkDocs, package build, and Twine: passed
- fresh-wheel CLI and workbench import smoke: passed

Publication and hosted validation:

- PR #45 complete CI matrix: passed
- tag `v2.8.0` points to merged `main` commit `0633834`
- Trusted Publishing to TestPyPI and PyPI: passed
- fresh no-cache public PyPI install reports `openpkflow 2.8.0`
- public CLI smoke: f1 `2.000`, f2 `92.47`; workbench import passed
- Cloudflare frontend and GitHub Pages docs: HTTP 200
- Render `/health` and `/openapi.json`: v2.8.0, branch `main`, service
  `srv-d8fb63navr4c73a3gclg`. The release first converged at `0633834`;
  documentation-only merges also redeploy Render, so `/health.git_sha` is the
  source of truth for the current deployed `main` commit.
- production OpenAPI inventory: **32 paths**

Dependency re-check on 2026-07-30:

- npm reports 7.18.1 as the latest `react-router-dom` release.
- `npm audit` flags GHSA-qwww-vcr4-c8h2 for versions from 7.12.0 through
  8.2.0, but the advisory affects unstable RSC APIs. OpenPKFlow is a client-only
  Vite SPA and uses neither RSC mode nor server actions.
- The advisory's patched 8.3.0 release is not available from npm. Do not force
  the suggested downgrade; re-check when an applicable patched release exists.

## Deployment

| Piece | URL | Verified public state |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | v2.8.0 surface, HTTP 200 |
| Backend | https://openpkflow.onrender.com | v2.8.0 from `main`, 32 paths |
| Docs | https://priyamthakar.github.io/openpkflow/ | v2.8.0 docs, HTTP 200 |
| PyPI | https://pypi.org/project/openpkflow/2.8.0/ | public install verified |

### Free Render free-tier ops (keep-warm + cold starts)

Render free web services **sleep after ~15 minutes** with no traffic. That is
normal free-tier behaviour, not a broken deploy.

**Operating decision:** retain the 10-minute keep-warm workflow for the public
OpenPKFlow portfolio/demo. It improves the first visit for recruiters,
collaborators, and evaluators, but it is not a production uptime mechanism.

| Piece | What it does | Notes |
| --- | --- | --- |
| GitHub Actions `Keep Render warm` | GET `/health` about every **10 minutes** | Workflow: `.github/workflows/keep-warm.yml`. Merged via [PR #50](https://github.com/priyamthakar/openpkflow/pull/50). |
| Frontend TopBar health badge | Retries, auto-polls while offline, click-to-retry | Merged via [PR #49](https://github.com/priyamthakar/openpkflow/pull/49). Survives residual cold starts. |
| Cloudflare Workers frontend | Static SPA only | Does **not** send keep-warm pings and does **not** email Gmail. |

**Does not email you every 10 minutes.** Successful keep-warm runs are silent.
GitHub may email only if the workflow **fails** and your notification settings
include failed Actions (repo Settings -> Notifications).

Manual keep-warm: Actions -> **Keep Render warm** -> Run workflow.
Run history: <https://github.com/priyamthakar/openpkflow/actions/workflows/keep-warm.yml>

This is **best-effort free keep-warm**, not a paid always-on SLA. GitHub cron can
drift; cold starts can still happen after deploys or rare missed pings.

Render currently grants 750 shared free instance-hours per workspace each
calendar month. One continuously warm service uses about 720 hours in a 30-day
month or 744 hours in a 31-day month. Monitor Render's monthly usage and
disable or reassess keep-warm before adding another free web service to the
same workspace. If dependable production availability becomes a requirement,
use a paid always-on instance instead of tightening the ping schedule.

Current platform references:

- Render free-instance behaviour and limits: <https://render.com/docs/free>
- GitHub scheduled-workflow caveats: <https://docs.github.com/en/actions/how-tos/troubleshoot-workflows>

## Single next objective

Keep v2.8.0 stable while collecting real workbench feedback. Before accepting
another feature milestone:

1. triage real user feedback and remaining validation gaps;
2. require evidence of user value and independent validation before selecting
   new scientific scope;
3. await maintainer review on conda-forge staged-recipes PR
   [#33461](https://github.com/conda-forge/staged-recipes/pull/33461);

**Ops polish (done):** health badge cold-start recovery ([PR #49](https://github.com/priyamthakar/openpkflow/pull/49));
free keep-warm pings on `main` ([PR #50](https://github.com/priyamthakar/openpkflow/pull/50)).

Richer grid controls (row deletion, resize, drag fill) remain demand-gated.
Do not extend the frozen `pop/estimation/` module.

## Constraints

- Do not extend `pop/estimation/`; bug fixes only.
- Do not add EMA ABEL, full-replicate RSABE, NTI decisions, or unvalidated
  formal BE designs.
- Preserve explicit AUC method and BLQ handling.
- Keep pharmacometric logic in `src/openpkflow/`, never in `api/` or `webapp/`.
- Do not use `--no-verify`, force-push, or amend published commits.
- Work directly on `main` in the `D:\openpkflow` checkout (single-branch
  workflow since the 2026-09-06 consolidation).
