# Session Summary - 2026-07-28

## Objective

Begin the user-approved path from v2.7.1 through v2.8.0, stopping at the next
safe checkpoint and synchronizing the living documentation and future plans.

## Initial reconciled state

- Latest public package and GitHub release: v2.7.0.
- `origin/main`: `c14ac2e`, including merged FastAPI dependency PR #42.
- Conda-forge PR #33461: open, green, awaiting maintainer review.
- Render: still stale at engine 2.6.0; hosted convergence remains unverified.
- Original checkout: preserved, including its user-owned untracked file.
- Release worktree: `D:\openpkflow-v2.7.1-v2.8.0`,
  branch `release/v2.7.1`.

## v2.7.1 work completed

- Added version and Git provenance to `/health`.
- Added a fail-closed production convergence script and scheduled/manual
  workflow.
- Added focused Playwright tests for chart legend restoration, PNG export,
  sidebar persistence, and mobile navigation.
- Reused the shared `EmptyResults` component across remaining result panes.
- Assigned package metadata and changelogs to 2.7.1.
- Synchronized the living documentation spine and bounded the v2.8.0 plan.

## Verification at the initial checkpoint

- Ruff lint and format: passed.
- mypy: 84 source files, passed.
- API: 55 passed.
- Full standard non-MCMC suite: 1,313 passed, 22 deselected.
- frontend lint/build: passed.
- Playwright: 19 passed.
- Strict MkDocs, pre-commit, final build/Twine, and fresh-wheel CLI smoke:
  passed.
- At that checkpoint, commit/PR/CI and the remaining publication/deployment
  gates had not yet been completed. They were completed later in the same
  continuing run, as recorded below.

## Release outcome

v2.7.1 was published through PR #43, squash-merged as `d24263d`, tagged, and
released on GitHub. Trusted Publishing run 30334756702 completed successfully
for TestPyPI and PyPI. A fresh public-index installation and CLI smoke passed.
Render, Cloudflare, and documentation convergence were verified; Render reports
version 2.7.1 and commit `d24263d`.

The initial PR API job caught a Linux import-path defect in the production smoke
test. Moving the reusable verifier into the installed
`openpkflow.validation.deployment` module fixed the root cause, and the full CI
matrix passed.

## Resume

The v2.7.1 publication-state documentation sync was merged as `e49e3f9`.
The v2.8.0 Advanced Dissolution Workbench candidate is now implemented in the
isolated `release/v2.8.0` worktree. It includes core orchestration, complete
reports, audit ZIP, three API endpoints, an editable React workflow, focused
core/API/browser tests, and synchronized documentation.

The final settled-tree matrix passed. PR #45 was squash-merged as `0633834`,
tagged `v2.8.0`, and published through Trusted Publishing run 30509130768.
A fresh no-cache public installation, CLI/workbench smoke, Cloudflare frontend,
GitHub Pages docs, and Render version/commit convergence all passed. Render
reports v2.8.0 at `0633834` with 32 OpenAPI paths.

The post-release documentation sync is on `docs/v2.8.0-release`. The next
objective is stability and real workbench feedback; richer grid controls and
new feature scope remain demand- and evidence-gated.
