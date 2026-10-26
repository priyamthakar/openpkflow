# OpenPKFlow Handoff

**Last updated:** 2026-10-26

## v2.9.0 release (2026-10-04)

OpenPKFlow **v2.9.0 is published and hosted convergence is verified**.

- Fix PR [#61](https://github.com/priyamthakar/openpkflow/pull/61) (`3a7f4e2`):
  workbench MSD always "similar" (degenerate mean-only MSD) replaced by
  vessel-level `msd_vessels()`; bootstrap f2 85% rule; all-BLQ NCA crash;
  sparse fit initial guess; API temp files; PKNCA lambda_z tolerance;
  disprofas and PKNCA cross-validation scripts.
- Release PR [#62](https://github.com/priyamthakar/openpkflow/pull/62)
  (`02600a7`): exact BE power (Owen's Q, PowerTOST to 1e-9); `include_tmax`
  closes all WinNonlin lambda_z exclusions; `openpkflow nca run`; analytic
  sparse AUClast; bootstrap f2 note; workbench MSD limit setting; paste-grid
  controls; stable log trapezoid.
- GitHub Release and tag `v2.9.0` at `02600a7`; Trusted Publishing
  [run 37172605110](https://github.com/priyamthakar/openpkflow/actions/runs/37172605110)
  passed; fresh public `pip install openpkflow==2.9.0` verified.
- Hosted convergence verified 2026-10-26: Render `/health` reported
  `engine_version` 2.9.0 at `main` commit `fe622c1`, and `/openapi.json`
  reported 2.9.0 with 32 paths. The deployed `git_sha` follows the latest
  `main`, not the tag, so every later merge changes it; `/health` stays the
  source of truth.

## Post-v2.9.0 maintenance (2026-10-26)

- PR [#66](https://github.com/priyamthakar/openpkflow/pull/66): `fastapi>=0.143.2`.
- PR [#67](https://github.com/priyamthakar/openpkflow/pull/67): the
  scheduled `Production convergence` job failed on 7 of 8 runs from 2026-10-18
  to 2026-10-25. Every failure was the same `/health` read timeout at the 30 s
  per-request limit, consistent with a free-tier cold start; a manual check on
  2026-10-26 found the deployment healthy. The job now wakes Render with the
  keep-warm retry loop and runs the check with `--timeout 120`.
- PR [#68](https://github.com/priyamthakar/openpkflow/pull/68): the webapp
  lockfile moves `react-router` and `react-router-dom` from 7.18.1 to 7.18.4
  (GHSA-qwww-vcr4-c8h2 is patched in 7.18.2). A second commit runs
  `npm audit fix` within existing ranges (vite 8.3.5, rolldown 1.2.15, zod
  4.6.7 and other build tooling), so `npm audit` reports 0 vulnerabilities.
- conda-forge staged-recipes PR
  [#33461](https://github.com/conda-forge/staged-recipes/pull/33461) is waiting
  on the author, not on maintainers. It has been labelled "Awaiting author
  contribution" since 2026-09-30, after the reviewer asked on 2026-09-11 for the
  v1 `recipe.yaml` format. The recipe still targets 2.7.0.

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

## v2.8.0 release (2026-07-30)

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

## v2.8.0 verification evidence

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

Dependency re-check on 2026-07-30: `npm audit` flagged GHSA-qwww-vcr4-c8h2
(unstable RSC APIs, unused by this client-only SPA) with no 7.x patch available.
Resolved on 2026-10-26: the advisory is patched in `react-router` 7.18.2 and the
lockfile moved to 7.18.4 in PR
[#68](https://github.com/priyamthakar/openpkflow/pull/68).

## Deployment

| Piece | URL | Verified public state |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | auto-deploys from `main`, HTTP 200 (2026-10-26) |
| Backend | https://openpkflow.onrender.com | v2.9.0 from `main`, 32 paths (2026-10-26) |
| Docs | https://priyamthakar.github.io/openpkflow/ | v2.9.0 docs, HTTP 200 |
| PyPI | https://pypi.org/project/openpkflow/2.9.0/ | v2.9.0 public install verified 2026-10-04 |

### Free Render free-tier ops (keep-warm + cold starts)

Render free web services **sleep after ~15 minutes** with no traffic. That is
normal free-tier behaviour, not a broken deploy.

**Operating decision:** retain the 10-minute keep-warm workflow for the public
OpenPKFlow portfolio/demo. It improves the first visit for recruiters,
collaborators, and evaluators, but it is not a production uptime mechanism.

| Piece | What it does | Notes |
| --- | --- | --- |
| GitHub Actions `Keep Render warm` | GET `/health`, scheduled every 10 minutes (runs far less often; see below) | Workflow: `.github/workflows/keep-warm.yml`. Merged via [PR #50](https://github.com/priyamthakar/openpkflow/pull/50). |
| Frontend TopBar health badge | Retries, auto-polls while offline, click-to-retry | Merged via [PR #49](https://github.com/priyamthakar/openpkflow/pull/49). Survives residual cold starts. |
| Cloudflare Workers frontend | Static SPA only | Does **not** send keep-warm pings and does **not** email Gmail. |

**Does not email you every 10 minutes.** Successful keep-warm runs are silent.
GitHub may email only if the workflow **fails** and your notification settings
include failed Actions (repo Settings -> Notifications).

Manual keep-warm: Actions -> **Keep Render warm** -> Run workflow.
Run history: <https://github.com/priyamthakar/openpkflow/actions/workflows/keep-warm.yml>

This is **best-effort free keep-warm**, not a paid always-on SLA.

**Measured cadence (2026-10-26):** the 10-minute schedule produced only 8 runs
between 2026-10-25 00:00 UTC and 2026-10-26 02:00 UTC, roughly one every 2-3
hours. Those gaps exceed Render's idle-sleep threshold, so the workflow cannot
reliably prevent sleep, and first visits after quiet periods may still hit a
cold start. Whether to accept this or move the ping to a more reliable
scheduler is an open owner decision.

Render currently grants 750 shared free instance-hours per workspace each
calendar month. A continuously warm service would use about 720 hours in a
30-day month or 744 hours in a 31-day month; actual use depends on real traffic
as well as pings. Monitor Render's monthly usage and
disable or reassess keep-warm before adding another free web service to the
same workspace. If dependable production availability becomes a requirement,
use a paid always-on instance instead of tightening the ping schedule.

Current platform references:

- Render free-instance behaviour and limits: <https://render.com/docs/free>
- GitHub scheduled-workflow caveats: <https://docs.github.com/en/actions/how-tos/troubleshoot-workflows>

## Single next objective

Keep v2.9.0 stable while collecting real workbench feedback. Before accepting
another feature milestone:

1. triage real user feedback and remaining validation gaps;
2. require evidence of user value and independent validation before selecting
   new scientific scope;
3. finish conda-forge staged-recipes PR
   [#33461](https://github.com/conda-forge/staged-recipes/pull/33461), which is
   waiting on the author: convert the recipe to v1 `recipe.yaml`, move it to
   2.9.0, and ask for review again;
4. decide whether the measured keep-warm cadence is acceptable.

**Ops polish (done):** health badge cold-start recovery ([PR #49](https://github.com/priyamthakar/openpkflow/pull/49));
free keep-warm pings on `main` ([PR #50](https://github.com/priyamthakar/openpkflow/pull/50));
convergence check wakes Render before checking ([PR #67](https://github.com/priyamthakar/openpkflow/pull/67)).

v2.9.0 added grid row selection, bulk delete and fill down; column resize and
drag fill remain demand-gated.
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
