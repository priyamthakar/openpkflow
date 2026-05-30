# Release Workflow

This checklist is for OpenPKFlow v2.x releases. It is intentionally short:
v2.4 is a credibility sprint focused on trust, usability, and release discipline,
not broad new scientific scope.

## Release principles

- Keep v2.x additive and avoid breaking API changes before v3.0.0.
- Treat `docs/changelog.md` as the source for GitHub release notes.
- Keep regulatory language precise: OpenPKFlow supports transparent,
  reproducible analysis; it does not replace validated jurisdiction-specific
  workflows or expert review.
- Keep static validation docs free of local verification snapshots that will
  drift over time.

## Pre-release checks

1. Confirm the version is updated in project metadata and package exports.
2. Confirm `docs/changelog.md` has a dated release section with user-facing
   changes, caveats, and migration notes.
3. Run `python scripts/release_readiness.py` before tagging. Warnings are
   acceptable before the tag/release exists; failures must be fixed.
4. Run the standard test suite and any manual or nightly slow validation checks
   needed for the release scope.
   - Standard: `python -m pytest -q`
   - Slow validation: `python -m pytest -m slow tests/validation -q`
5. Build the documentation site with `mkdocs build --strict`.
6. Confirm package artifacts build cleanly and inspect metadata.
7. Confirm PyPI, GitHub release, and conda-forge state before announcing.

## GitHub release notes

Use the matching section from `docs/changelog.md`. Keep notes concise and
include:

- What changed.
- What users need to do.
- Validation or regulatory caveats, especially for research-grade workflows.

## v2.4 readiness focus

- Replicate BE screening must remain clearly labelled as research-grade until
  full FDA/EMA parity is validated against reference SAS/R workflows.
- Release notes should emphasize external-reference validation, reportability,
  and clearer boundaries around regulatory use.
- Documentation should state what OpenPKFlow is and is not before making
  capability claims.
