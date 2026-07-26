# Release Workflow

This checklist is for OpenPKFlow v2.x releases. Keep it short and mechanical.

## Current release state

**v2.7.0 was published on 2026-07-25.** It packages sparse NCA, pipeline audit
bundles, formal BE ANOVA, validated FDA partial-replicate RSABE, MAP/SUPAC web
workflows, and web design polish.

- Release PR: <https://github.com/priyamthakar/openpkflow/pull/39>
- Release commit: `74039b41054f7caee9a4f64d53a6d0cd455c5903`
- GitHub Release: <https://github.com/priyamthakar/openpkflow/releases/tag/v2.7.0>
- PyPI: <https://pypi.org/project/openpkflow/2.7.0/>
- Trusted Publishing run:
  <https://github.com/priyamthakar/openpkflow/actions/runs/30167426746>
- Conda-forge staged-recipes PR:
  <https://github.com/conda-forge/staged-recipes/pull/33461>
- Deployment check (2026-07-26): frontend and docs return HTTP 200; Render is
  reachable but `/health` still reports engine version 2.6.0. Manually redeploy
  from `main` and verify 2.7.0 before claiming backend release convergence.

See `HANDOFF.md` for full takeover context.

## Release principles

- Keep v2.x additive; avoid breaking API changes before v3.0.0.
- Treat `docs/changelog.md` as the source for GitHub release notes (keep
  `CHANGELOG.md` in sync).
- Keep regulatory language precise: OpenPKFlow supports transparent,
  reproducible analysis; it does not replace validated jurisdiction-specific
  workflows or expert review (see `docs/positioning.md`).
- Do not overclaim RSABE, Part 11, or FDA approval.
- Keep static validation docs free of local verification snapshots that will
  drift over time.
- Never use `--no-verify` to bypass hooks when cutting a release commit.

## Pre-release checks

1. Confirm version is **identical** in:
   - `pyproject.toml`
   - `src/openpkflow/__init__.py`
   - `CHANGELOG.md` and `docs/changelog.md` dated section
2. Confirm `docs/changelog.md` has a dated release section with user-facing
   changes, caveats, and migration notes.
3. Run `python scripts/release_readiness.py` before tagging. Warnings are
   acceptable before the tag/release exists; failures must be fixed.
4. Run tests:
   - Standard: `python -m pytest --ignore=tests/pop/test_saem.py --ignore=tests/bayes/test_bayes_be.py -k "not MCMC and not mcmc" -q`
   - Optional slow: `python -m pytest -m slow tests/validation -q`
   - API: `cd api && python -m pytest -q`
5. Build docs: `mkdocs build --strict`
6. Build package: `python -m build && python -m twine check dist/*`
7. Confirm PR is merged to `main` and CI is green on `main`.
8. Confirm PyPI, GitHub release, and conda-forge state before announcing.

## GitHub release notes

Use the matching section from `docs/changelog.md`. Include:

- What changed.
- What users need to do.
- Validation or regulatory caveats (especially research-grade tools).

## Tag and publish order

1. Merge PR to `main`
2. On `main`: final `release_readiness.py` + green CI
3. Tag the current target and push the tag
4. Confirm GitHub Actions release / Trusted Publishing workflow
5. Verify the exact PyPI version in a fresh environment, then run CLI smoke checks
6. Update conda-forge feedstock if automated PR does not appear promptly

## v2.7.0 specific caveats for notes

- SUPAC classification and alcohol dose-dumping helpers are **screening** tools,
  not full guidance automation.
- Formal complete balanced 2x2 ANOVA is supported. FDA partial-replicate RSABE is
  validated against Patterson and Jones (2012), Table II for complete balanced
  TRR/RTR/RRT allocation. Low-CV data return `NOT_EVALUABLE` for standard ABE
  routing; unbalanced or incomplete data fail closed.
- Pop PK FOCE-I/SAEM is research-grade and frozen for extension.
- Study pipeline composes existing modules; stages without inputs are skipped.

## Post-release agent handoff

Update `HANDOFF.md`, `SESSION_SUMMARY_<date>.md`, AGENTS.md, CLAUDE.md,
ROADMAP.md, and `progress_web_app.md` with the released version, verified checks,
active branch, incomplete work, and exact resume commands.
