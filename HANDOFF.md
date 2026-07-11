# OpenPKFlow Handoff

**Current version in tree:** 2.6.0 package metadata (`pyproject.toml`, `CITATION.cff`) on `main` at `5433882`. The correction sprint has landed and merged directly to `main` (branch `fix/v2.6.0-correction-hardening` is deleted); no divergent branches remain except `gh-pages`.

**Do not tag v2.6.0 yet.** Code is complete and the full test suite passes (1273 passed), but the release-hardening checklist below is not finished. PyPI's latest published release is still 2.5.0 -- verify this hasn't changed before trusting any "current version" claim elsewhere in the docs.

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

### Still open (Priority 1 CI / Priority 2 release)

- CI: remove `mypy continue-on-error` -- blocked on 69 pre-existing errors, mostly in frozen `pop/estimation/` and `student/`; needs its own triage pass, not a blind flag removal
- CI: Codecov auth, API/frontend test jobs, Python 3.13 + Windows smoke
- Public API upload limits / security headers
- `conda-forge` recipe: verify the feedstock -- `anaconda.org/conda-forge/openpkflow` currently 404s despite ROADMAP.md previously claiming it was live
- GitHub Release for v2.5.0 (manual owner step, cannot be automated)
- Git tag `v2.6.0` + PyPI publish -- gated on the above

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
