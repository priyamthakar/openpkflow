# OpenPKFlow Handoff

**Current version in tree:** 2.5.0 package metadata on `main` at PR #27 merge (`2eed9d7`); correction sprint branch `fix/v2.6.0-correction-hardening`.

**Do not tag v2.6.0 yet.** Feature merge (#27) is on `origin/main`, but scientific correctness and release-hardening issues remain.

## Correction sprint (2026-07-11)

Started from clean, updated `main` at `2eed9d7` (not the divergent `feat/v2.6.0-improvement-sprint` at `4d49958`).

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

### Still open (Priority 0 product / Priority 1 CI)

- Vite high-severity advisory (npm audit / lockfile update)
- Full HANDOFF/ROADMAP/docs claim scrub (conda-forge live, v2.5 GitHub Release)
- CI: remove mypy continue-on-error, Codecov auth, API/frontend jobs, Python 3.13 + Windows smoke
- publish.yml tag-must-match-main hardening
- Public API upload limits / security headers
- Remaining analysis pages (BE, Dissolution, Sim) stale-result snapshot pattern
- GitHub Release for v2.5.0 (manual owner step)

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
