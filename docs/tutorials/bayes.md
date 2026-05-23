# Tutorial: Bayesian PK

This tutorial covers MAP individual PK estimation, full Bayesian posterior
sampling, and Bayesian 2x2 crossover bioequivalence using OpenPKFlow.

---

## 1. Setting up priors

`PKPrior` defines log-normal priors for a 1-compartment model. The defaults
are weakly informative and suitable for many small-molecule drugs:

```python
from openpkflow.bayes import PKPrior

# Default priors
prior = PKPrior()
print(f"CL prior: log-normal(mean={prior.log_cl_mean:.3f}, sd={prior.log_cl_sd})")
print(f"Vz prior: log-normal(mean={prior.log_v_mean:.3f}, sd={prior.log_v_sd})")
```

Tighten priors when you have population estimates from prior studies:

```python
prior = PKPrior(
    log_cl_mean=1.791,   # log(6.0) --> prior CL ~ 6 L/h
    log_cl_sd=0.3,       # tighter SD
    log_v_mean=3.688,    # log(40.0) --> prior Vz ~ 40 L
    log_v_sd=0.3,
)
```

---

## 2. MAP individual PK estimation

MAP estimation uses L-BFGS-B optimisation and works with the base install
(no extras required). It is suitable for sparse-sampling scenarios with
3-5 data points:

```python
from openpkflow.bayes import map_individual_pk

times = [0.5, 1.0, 2.0, 4.0, 8.0]
concentrations = [4.4, 9.8, 16.6, 16.1, 4.8]
dose = 100.0

result = map_individual_pk(
    times,
    concentrations,
    dose,
    route="oral",
    prior=prior,
    subject="S01",
)

print(result.summary())
```

The `summary()` output includes:

- MAP parameter estimates with standard errors
- Derived PK parameters (t1/2, AUCinf, Cmax, Tmax)
- Convergence diagnostics (gradient norm, Hessian condition)
- Any diagnostic warnings

### Interpreting the output

```python
if not result.converged:
    print("WARNING: Optimiser did not converge. Do not interpret as MAP.")

if not result.uncertainty_reliable:
    print("WARNING: Standard errors are unreliable (non-positive-definite Hessian).")

for warning in result.warnings:
    print(f"[!] {warning}")

print(f"CL_F = {result.CL_F:.2f} +/- {result.CL_F_se:.2f} L/h")
print(f"Vz_F = {result.Vz_F:.2f} +/- {result.Vz_F_se:.2f} L")
print(f"ka   = {result.ka:.3f} +/- {result.ka_se:.3f} 1/h")
print(f"t1/2 = {result.half_life:.2f} h")
print(f"AUCinf = {result.AUCinf:.2f} h*mcg/mL")
```

### Plotting and reporting

```python
result.plot(show=True)

result.report("map_report.html")
result.report("map_report.md", format="markdown")
```

---

## 3. Full Bayesian posterior sampling

For full uncertainty quantification, use `bayes_individual_pk`. This
requires PyMC (`pip install openpkflow[bayes]`):

```python
from openpkflow.bayes import bayes_individual_pk

result = bayes_individual_pk(
    times,
    concentrations,
    dose,
    route="oral",
    prior=prior,
    n_samples=2000,
    tune=1000,
    chains=2,
    subject="S01",
)

print(result.summary())
```

The output includes posterior means with 95% credible intervals:

```python
print(f"CL_F posterior mean = {result.cl_mean:.2f} [95% CrI: "
      f"{result.cl_95ci[0]:.2f}, {result.cl_95ci[1]:.2f}] L/h")
print(f"Vz_F posterior mean = {result.v_mean:.2f} [95% CrI: "
      f"{result.v_95ci[0]:.2f}, {result.v_95ci[1]:.2f}] L")
```

### Shrinkage assessment

The shrinkage metric tells you how much the posterior is pulled toward the
prior (0 = data-dominated, 1 = prior-dominated):

```python
print(f"CL shrinkage toward prior: {result.shrinkage_cl:.1%}")
```

High shrinkage (> 50%) indicates sparse or noisy data.

---

## 4. Convergence diagnostics

PyMC-based results compute effective sample size (ESS) and R-hat
automatically. Diagnostic warnings are included in `result.warnings`:

```python
for w in result.warnings:
    print(f"[!] {w}")
```

Guidelines:

- **R-hat < 1.05**: Chains have converged. Values > 1.05 indicate
  non-convergence; increase `tune` or `n_samples`.
- **ESS > 100 * chains**: Effective sample size is adequate. Low ESS
  means the chain is highly autocorrelated; increase `n_samples` or `tune`.

If you need direct access to posterior samples for custom diagnostics:

```python
import numpy as np
cl_samples = result.cl_posterior
v_samples = result.v_posterior

print(f"CL CV: {np.std(cl_samples) / np.mean(cl_samples):.1%}")
print(f"CL-V correlation: {np.corrcoef(cl_samples, v_samples)[0, 1]:.3f}")
```

---

## 5. Bayesian BE analysis

`bayes_be` fits a Bayesian 2x2 crossover model via PyMC NUTS and computes
P(0.80 <= GMR <= 1.25) -- the posterior probability of bioequivalence.

First, prepare a DataFrame with the required columns:

```python
import pandas as pd

data = pd.DataFrame({
    "subject": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8,
                9, 9, 10, 10, 11, 11, 12, 12],
    "sequence": ["RT", "RT", "RT", "RT", "RT", "RT", "RT", "RT", "RT", "RT",
                 "TR", "TR", "TR", "TR", "TR", "TR", "TR", "TR", "TR", "TR",
                 "TR", "TR", "TR", "TR"],
    "period": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2,
               1, 2, 1, 2, 1, 2, 1, 2],
    "treatment": ["R", "T", "R", "T", "R", "T", "R", "T", "R", "T",
                  "T", "R", "T", "R", "T", "R", "T", "R", "T", "R",
                  "T", "R", "T", "R"],
    "value": [105, 110, 88, 92, 120, 115, 95, 100, 78, 85,
              118, 112, 102, 98, 85, 80, 130, 125, 92, 88,
              107, 103, 76, 72],
})
```

Run the analysis:

```python
from openpkflow.bayes import bayes_be

result = bayes_be(
    data,
    metric="AUC",
    n_samples=2000,
    tune=1000,
    chains=2,
)

print(result.summary())
```

The summary displays side-by-side Bayesian and frequentist results:

```python
print(f"Bayesian P(BE) = {result.p_be:.3f}")
print(f"  GMR = {result.gmr_mean:.4g} [95% CrI: "
      f"{result.gmr_95ci[0]:.4g}, {result.gmr_95ci[1]:.4g}]")
print(f"Frequentist GMR = {result.freq_gmr:.4g} [90% CI: "
      f"{result.freq_90ci[0]:.4g}, {result.freq_90ci[1]:.4g}]")
```

### Bayesian BE reporting

```python
result.report("bayes_be_report.html")
result.report("bayes_be_report.md", format="markdown")
```

---

## 6. Choosing MAP vs full Bayesian

| Consideration | MAP (map_individual_pk) | Full Bayesian (bayes_individual_pk) |
|---------------|--------------------------|--------------------------------------|
| Dependencies | Base install only | Requires `openpkflow[bayes]` (PyMC) |
| Runtime | < 1 second | 30-120 seconds (MCMC) |
| Output | Point estimates + SEs | Full posterior distributions |
| Uncertainty | Quadratic approximation (Hessian) | Exact posterior via MCMC |
| Uses | Quick fit, diagnostics, reports | Full inference, credible intervals |

MAP estimation is the recommended starting point. Move to full Bayesian
sampling when you need posterior probabilities, asymmetric credible intervals,
or full uncertainty propagation.

---

## Regulatory notes

- Bayesian PK results are exploratory. Regulatory submissions require
  validated population PK software (NONMEM, Monolix, Phoenix NLME).
- Bayesian BE is not accepted by most regulators as a standalone BE method.
  The frequentist 90% CI is provided alongside for comparison.
- MAP estimation is useful for study design, model diagnostics, and
  internal decision-making. Do not submit MAP-derived parameters in
  lieu of a full population PK analysis.
