# openpkflow.bayes

Bayesian PK estimation: MAP individual PK, full posterior sampling via MCMC, and Bayesian 2x2 crossover bioequivalence.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `PKPrior` | dataclass | Log-normal priors for PK parameters; `.log_prior_oral()`, `.log_prior_iv()` |
| `map_individual_pk(times, concentrations, dose, route, prior, ...)` | function | MAP estimation via scipy L-BFGS-B (base install -- no extras needed) |
| `MapPKResult` | dataclass | MAP result: parameters, SEs, diagnostics; `.summary()`, `.plot()`, `.report()` |
| `bayes_individual_pk(times, concentrations, dose, route, prior, ...)` | function | Full posterior MCMC via PyMC Metropolis-Hastings (requires `openpkflow[bayes]`) |
| `BayesPKResult` | dataclass | Posterior samples, means, 95% CrIs; `.summary()`, `.to_dict()` |
| `bayes_be(data, metric, ...)` | function | Bayesian 2x2 crossover BE via PyMC NUTS; returns `BayesBEResult` (requires `openpkflow[bayes]`) |
| `BayesBEResult` | dataclass | Posterior GMR, P(BE), frequentist comparison; `.summary()`, `.report()`, `.to_dict()` |

## Install

MAP estimation works with the base install:

```bash
pip install openpkflow
```

For full posterior sampling (PyMC):

```bash
pip install openpkflow[bayes]
```

To check at runtime whether PyMC is available:

```python
from openpkflow.bayes import _require_pymc
_require_pymc()  # raises ImportError if PyMC is not installed
```

## PKPrior defaults

| Field | Default | Description |
|-------|---------|-------------|
| `log_cl_mean` | `1.609` | Prior mean of log(CL) or log(CL_F) (~ 5.0 L/h) |
| `log_cl_sd` | `1.0` | Prior SD on log(CL) |
| `log_v_mean` | `3.912` | Prior mean of log(Vz) or log(Vz_F) (~ 50.0 L) |
| `log_v_sd` | `1.0` | Prior SD on log(Vz) |
| `log_ka_mean` | `0.0` | Prior mean of log(ka) (~ 1.0 1/h) |
| `log_ka_sd` | `1.0` | Prior SD on log(ka) |
| `sigma_mean` | `0.2` | Fixed proportional residual error (CV fraction) |
| `log_cl_bounds` | `(-6, 6)` | Log-space optimisation bounds for CL |
| `log_v_bounds` | `(-2, 8)` | Log-space optimisation bounds for Vz |
| `log_ka_bounds` | `(-4, 4)` | Log-space optimisation bounds for ka |

## MAP diagnostics

`map_individual_pk` performs these checks automatically and populates the `warnings` list:

| Diagnostic | Threshold | Warning if |
|------------|-----------|------------|
| Optimiser convergence | L-BFGS-B success flag | Not converged |
| Gradient norm | `< 1e-3` | Solution may not be at stationary point |
| Multi-start agreement | `> 20%` spread | Model may not be identifiable |
| Prior dominance | Data LL < 10% of posterior | MAP reflects prior more than data |
| Hessian condition | `> 1e6` | Near-singular; SEs unreliable |
| Hessian definiteness | All eigenvalues > 0 | SEs not estimable |
| Parameter at bound | `< 1%` of bound span | Estimate constrained by bounds |

## Bayesian BE decision threshold

| P(0.80 <= GMR <= 1.25) | Verdict |
|-------------------------|---------|
| >= 0.95 | PASS |
| >= 0.80 | BORDERLINE |
| < 0.80 | FAIL |

The report also shows the frequentist 90% CI for side-by-side comparison.

## Report formats

**MapPKResult:**
`.report("out.html")` -- HTML
`.report("out.md")` -- Markdown
(PDF and DOCX planned for v2.1.0)

**BayesBEResult:**
`.report("out.html", format="html")` -- HTML with GMR posterior histogram
`.report("out.md", format="markdown")` -- Markdown

## Notes

- MAP estimation uses analytical 1-cmt closed-form model equations (not ODEs).
  Multi-start L-BFGS-B runs from three different starting points.
- Full Bayesian sampling uses Metropolis-Hastings (not NUTS) for PK fitting,
  because the PK model is a blackbox numpy function without PyTensor gradients.
- Bayesian BE uses a log-scale linear mixed model with NUTS sampling.
  The model includes fixed effects for sequence, period, and treatment,
  and random subject-within-sequence effects.
- MCMC convergence is assessed via ESS (effective sample size, minimum 100 * chains
  recommended) and R-hat (< 1.05 for convergence).
