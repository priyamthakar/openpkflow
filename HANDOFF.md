# OpenPKFlow Handoff

**Last updated:** 2026-07-25

## Current state

- Active milestone: **v2.7.0 release**.
- Release branch: `release/v2.7.0`, based on `origin/main` at `273e619`.
- v2.6.0 remains the latest published version until the v2.7.0 tag workflow
  completes.
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

The frontend production audit has one residual advisory family in React Router's
React Server Components action mode. OpenPKFlow is a client-only SPA and does not
use RSC or server actions. React Router 7.18.1 is the newest published
`react-router-dom` release; no patched `react-router-dom` version is currently
available. All other compatible audit fixes were applied.

## Deployment

| Piece | URL | Trigger |
| --- | --- | --- |
| Frontend | https://openpkflow.priyamthakar1.workers.dev | merge to `main` |
| Backend | https://openpkflow.onrender.com | merge to `main` |
| Docs | https://priyamthakar.github.io/openpkflow/ | docs workflow |
| PyPI | https://pypi.org/project/openpkflow/ | version tag workflow |

`webapp/.env.production` supplies the Render API URL. CORS is configured in
`render.yaml`. The frontend and backend deploy automatically after merge.

## Resume here

1. Commit and push `release/v2.7.0`.
2. Open the release PR and require green CI.
3. Merge the PR, tag the resulting `main` commit as `v2.7.0`, and push the tag.
4. Verify the GitHub Release, Trusted Publishing, PyPI, and fresh-install CLI.
5. Retarget conda-forge staged-recipes PR #33461 to v2.7.0 and wait for its
   platform builds.
6. Update this handoff with the final release commit, URLs, and post-release
   maintenance boundary.

## Constraints

- Do not extend `pop/estimation/`; bug fixes only.
- Do not add EMA ABEL, full-replicate RSABE, NTI decisions, or unvalidated formal
  BE designs.
- Preserve explicit AUC method and BLQ handling.
- Keep pharmacometric logic in `src/openpkflow/`, never in `api/` or `webapp/`.
- Do not use `--no-verify`, force-push, or amend published commits.
