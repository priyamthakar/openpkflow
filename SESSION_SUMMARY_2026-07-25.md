# Session Summary - 2026-07-25

## Objective

Prepare, validate, publish, and hand off OpenPKFlow v2.7.0 without adding a new
scientific feature.

## Release hardening

- Assigned the additive post-v2.6.0 work to v2.7.0.
- Fixed the flaky AUC scale-invariance property at the IEEE-754 subnormal boundary.
- Added an explicit regression showing that half of the smallest positive float
  underflows to zero.
- Updated compatible frontend dependency resolutions after a production audit.
- Reconciled RSABE reference, tutorial, validation, positioning, migration, agent,
  roadmap, release, and handoff documentation with the validated implementation.

## Validation

- 130 targeted NCA/BE/RSABE tests passed.
- 50 API tests passed.
- 1304 full-suite tests passed; 9 skipped and 22 deselected.
- 15 Playwright tests passed after frontend lint and production build.
- Ruff, formatting, mypy, pre-commit, strict MkDocs, build, and Twine checks passed.
- A clean wheel installed as openpkflow 2.7.0 and passed CLI smoke checks.

## Remaining release operations

See `HANDOFF.md` for the exact branch, release sequence, deployment URLs, residual
React Router RSC advisory context, and post-release conda-forge step.
