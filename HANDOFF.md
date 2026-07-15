# OpenPKFlow Handoff

**Current version in tree:** 2.6.0 package metadata (`pyproject.toml`, `CITATION.cff`). PR #27 and the correction sprint are on `main`; final release hardening is on `agent/v2.6-release-hardening` pending CI and merge.

**Do not tag v2.6.0 until the hardening branch is green on `main`.** The local release candidate passes 1275 standard tests plus API, browser, mypy, docs, build, and twine checks. PyPI's latest published release is still 2.5.0 as of 2026-07-15.

## Correction sprint (2026-07-11) -- COMPLETE, merged to main

### Completed in this sprint (library + packaging + key web fixes)

| Area | Status |
|------|--------|
| BE paired CV variance-halving | Done |
| NCA/pipeline fail-closed (AUC, BLQ, config keys, auc_tau) | Done |
| Transit model Savic structure + CL_F/Vz_F | Done |
| IVIVC unit conversion, no kel=0.1, no incomplete-dissolution rescale, single-form FDA verdict disabled | Done |
| Dissolution explicit f2_method (default regulatory) + persisted warnings | Done |
| SUPAC function-specific tables | Done |
| M13B Step 2 absolute SD > 8% | Done |
| Hatch sdist allowlist + .gitignore | Done |
| Webapp NCA/IVIVC stale-result report guard | Done |
| CITATION.cff -> 2.5.0; CHANGELOG Unreleased correction notes | Done |
| VALIDATION.md correction-sprint entries | Done |

### Also completed (2026-07-11, after the sprint above)

| Area | Status |
|------|--------|
| Vite high-severity advisory | Verified already resolved (`npm audit`: 0 vulnerabilities) |
| `publish.yml` tag-must-match-main hardening | Done -- refuses to publish unless the tag's commit is reachable from `main` |
| BE / Dissolution / Sim stale-result guard | Done -- extended the NCA/IVIVC pattern (BE/Dissolution: reset mutation on previously-missed inputs; Sim: disable download while a live re-fetch is in flight) |
| HANDOFF/ROADMAP/README/CHANGELOG doc scrub | Done -- see this commit; conda-forge claim was false (404 on anaconda.org, corrected in ROADMAP.md) |

### Release hardening (2026-07-15)

- Enforced mypy job added; non-frozen modules pass strict mypy. Frozen
  `pop/estimation/` has an explicit override until reactivation and validation.
- Codecov uploads verified; API/frontend jobs and Python 3.13 Linux/Windows smoke added.
- Upload reads are size-bounded and public API security headers are tested.
- Full-Omega label crash and unknown-route IV fallback fixed with regression tests.

### Still open

- `conda-forge/staged-recipes` PR #33461 is open with green checks but still targets
  2.3.0; no feedstock/package exists yet. Update it after v2.6.0 reaches PyPI.
- Merge the hardening PR after CI, then tag `v2.6.0` and verify Trusted Publishing.

The missing v2.5.0 GitHub Release was backfilled on 2026-07-15 from the existing tag.

### After corrections

Highest-value feature: study-pipeline web page, then downloadable audit bundle. Keep RSABE in BioEqPy; keep `pop/estimation` frozen.

## Quick commands

```bash
pip install -e ".[dev]"
pytest --ignore=tests/pop/test_saem.py --ignore=tests/bayes/test_bayes_be.py -k "not MCMC and not mcmc"
ruff check src/ tests/ --fix
```

## Identity

**Package:** openpkflow
**Author:** Priyam Thakar <priyamthakar1@gmail.com>
**GitHub:** https://github.com/priyamthakar/openpkflow
**Philosophy:** Transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting. Does not replace expert regulatory judgement.
