# Session Summary - 2026-07-26

## Objective

Refresh the living documentation against the public release, conda-forge, and
production deployment state after v2.7.0 publication.

## Verified state

- `main` starts at `a46194d`; v2.7.0 remains the latest GitHub and PyPI release.
- Conda-forge staged-recipes PR #33461 remains open, targets v2.7.0, and passes
  its linter plus Linux, Windows, and macOS builds.
- The Cloudflare frontend and GitHub Pages documentation return HTTP 200.
- The Render backend is reachable, but `/health` still reports engine version
  2.6.0 after multiple `main` merges.

## Documentation corrections

- Replaced the unsupported claim that Render is currently auto-converging from
  `main` with an explicit manual deployment/configuration gate.
- Made Render inspection and redeployment the first executable next step.
- Updated the API endpoint inventory and corrected the FDA RSABE validation
  scope.
- Updated the web application page inventory for FDA RSABE, MAP Individual PK,
  and SUPAC & Alcohol Screening.
- Preserved `SESSION_SUMMARY_2026-07-25.md` as the release-session record.

## Resume here

1. Open the Render service dashboard, inspect its repository/branch and latest
   build, and manually deploy current `main`.
2. Require both `/health` and `/openapi.json` to report version 2.7.0.
3. Await maintainer review of conda-forge staged-recipes PR #33461.
4. Keep `pop/estimation/` frozen; optional UI work remains bounded to regression
   coverage and shared empty-state polish.
