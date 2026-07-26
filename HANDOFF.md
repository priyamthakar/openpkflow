# OpenPKFlow Handoff

**Last updated:** 2026-07-26

## Current state

- Latest published release: **v2.7.0** (2026-07-25).
- Release PR: [#39](https://github.com/priyamthakar/openpkflow/pull/39), squash
  merged to `main` as `74039b4`.
- Tag: [`v2.7.0`](https://github.com/priyamthakar/openpkflow/releases/tag/v2.7.0),
  pointing to `74039b4`.
- PyPI: <https://pypi.org/project/openpkflow/2.7.0/>.
- Trusted Publishing:
  [run 30167426746](https://github.com/priyamthakar/openpkflow/actions/runs/30167426746)
  completed successfully for TestPyPI and PyPI.
- Conda-forge staged-recipes PR
  [#33461](https://github.com/conda-forge/staged-recipes/pull/33461) now targets
  v2.7.0; linter, Linux, Windows, and macOS checks all pass. It is awaiting
  maintainer review.
- Production verification on 2026-07-26:
  - frontend and documentation return HTTP 200
  - Render `/health` returns `status: ok` but `engine_version: 2.6.0`
  - the backend therefore needs a manual Render deployment/configuration check
    before v2.7.0 deployment can be claimed
- All feature work in this release is already merged:
  - PR #30: pipeline API, web workflow, and audit bundle
  - PR #31: sparse NCA validation, API, reports, and web workflow
  - PR #32: formal BE ANOVA, MAP PK, and SUPAC/alcohol workflows
  - PR #33: web design system and mobile polish
  - PR #35: validated FDA partial-replicate RSABE
- No new science module is part of the release PR.

## v2.7.0 release changes

- Version metadata and both changelogs are assigned to 2.7.0.
- The NCA AUC scale-invariance property excludes unrepresentable subnormal
  scaling and has an explicit IEEE-754 underflow regression.
- RSABE documentation now matches the validated implementation:
  - complete balanced TRR/RTR/RRT only
  - pinned to Patterson and Jones (2012), Table II
  - low CVwR returns `NOT_EVALUABLE` for standard ABE routing
  - unbalanced or incomplete studies fail closed
- Compatible frontend lockfile updates refresh React Router, PostCSS, Nano ID,
  and brace-expansion.

## Verification snapshot

Completed in the clean linked worktree `D:\openpkflow-v2.7.0-release`:

- Targeted NCA/BE/RSABE tests: **130 passed**
- API tests: **50 passed**, one expected sparse-fit covariance warning
- Full non-MCMC suite: **1304 passed, 9 skipped, 22 deselected**
- Frontend: ESLint clean, TypeScript/Vite build clean, **15 Playwright tests passed**
- Ruff lint and format check: clean
- mypy: **84 source files**, clean
- pre-commit: all hooks passed
- MkDocs strict build: passed
- Wheel/sdist: built and passed Twine checks
- Fresh wheel install:
  - `openpkflow version` -> `openpkflow 2.7.0`
  - `openpkflow similarity` -> f1 `2.000`, f2 `92.47`
- Fresh public-PyPI install:
  - installed `openpkflow==2.7.0` from `https://pypi.org/simple`
  - repeated the same version and similarity CLI smoke checks successfully

The frontend production audit has one residual advisory family in React Router's
React Server Components action mode. OpenPKFlow is a client-only SPA and does not
use RSC or server actions. React Router 7.18.1 is the newest published
`react-router-dom` release; no patched `react-router-dom` version is currently
available. All other compatible audit fixes were applied.

## Deployment

| Piece | URL | Trigger |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | merge to `main` |
| Backend | https://openpkflow.onrender.com | manual Render redeploy/configuration check required |
| Docs | https://priyamthakar.github.io/openpkflow/ | docs workflow |
| PyPI | https://pypi.org/project/openpkflow/ | version tag workflow |

`webapp/.env.production` supplies the Render API URL. CORS is configured in
`render.yaml`. The Cloudflare frontend and GitHub Pages documentation deploy
automatically. Render is reachable, but repeated checks after multiple `main`
merges still report engine version 2.6.0. Treat automatic Render deployment as
unverified: inspect the Render service connection/build history, trigger a manual
deploy from `main`, and require `/health` and `/openapi.json` to report 2.7.0.

## Resume here

1. Inspect or manually redeploy the Render service from `main`, then confirm both
   `/health` and `/openapi.json` report version 2.7.0.
2. Await maintainer review of conda-forge staged-recipes PR #33461.
3. Optionally add Playwright coverage for PKChart legend restoration and PNG
   export, sidebar collapse, and mobile navigation.
4. Keep `pop/estimation/` frozen and prioritize validation over new modules.

## Constraints

- Do not extend `pop/estimation/`; bug fixes only.
- Do not add EMA ABEL, full-replicate RSABE, NTI decisions, or unvalidated formal
  BE designs.
- Preserve explicit AUC method and BLQ handling.
- Keep pharmacometric logic in `src/openpkflow/`, never in `api/` or `webapp/`.
- Do not use `--no-verify`, force-push, or amend published commits.
