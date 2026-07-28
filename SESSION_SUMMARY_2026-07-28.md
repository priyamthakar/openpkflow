# Session Summary - 2026-07-28

## Objective

Begin the user-approved path from v2.7.1 through v2.8.0, stopping at the next
safe checkpoint and synchronizing the living documentation and future plans.

## Reconciled state

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

## Verification at stop point

- Ruff lint and format: passed.
- mypy: 84 source files, passed.
- API: 55 passed.
- Full standard non-MCMC suite: 1,313 passed, 22 deselected.
- frontend lint/build: passed.
- Playwright: 19 passed.
- Strict MkDocs, pre-commit, final build/Twine, and fresh-wheel CLI smoke:
  passed.
- Commit/PR/CI and the remaining publication/deployment gates have not yet been
  completed.

## Release boundary

v2.7.1 is a local release candidate, not a published release. No commit, push,
PR, tag, GitHub Release, PyPI publication, or deployment action was taken for
v2.7.1 in this session.

## Resume

Read `HANDOFF.md`, then resume with the release commit and PR workflow. Complete
every v2.7.1 publication and hosted-convergence gate before starting v2.8.0.
