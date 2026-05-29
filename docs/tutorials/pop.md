# Tutorial: Population PK

This tutorial covers FOCE-I and SAEM population PK parameter estimation,
goodness-of-fit (GOF) diagnostics, visual predictive checks (VPC), and
NONMEM-style dataset construction.

---

## 1. FOCE-I estimation (scipy tier, zero extra deps)

FOCE-I runs on the base install. It requires a NONMEM-format dataset with
`ID`, `TIME`, `DV`, `AMT`, and `EVID` columns.

```python
import pandas as pd
from openpkflow.pop import PopPKModel, run_foce_i
from openpkflow.datasets import example_theoph_path

# Load the built-in theophylline dataset (12 subjects, oral)
data = pd.read_csv(example_theoph_path())

# Define the model with initial estimates
model = PopPKModel(
    route="oral",
    fixed_effects={"CL_F": 4.0, "Vz_F": 30.0, "ka": 1.5},
    omega_diag={"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1},
    sigma_prop=0.15,
    sigma_add=0.0,
    error_model="combined",
    n_cmt=1,
    omega_type="diagonal",
)

result = run_foce_i(data, model)
print(result.summary())
```

The summary displays:

- Population typical values (CL_F, Vz_F, ka) with SE and RSE%
- IIV variances (omega^2) with SE
- Residual error (sigma_prop, sigma_add)
- Objective function (-2LL, AIC, BIC)
- EBE shrinkage per parameter

### Interpreting results

```python
# Parameter estimates
print(f"CL_F = {result.theta_pop['CL_F']:.3f} L/h")
print(f"Vz_F = {result.theta_pop['Vz_F']:.2f} L")
print(f"ka   = {result.theta_pop['ka']:.3f} 1/h")

# Diagnostics
print(f"-2LL = {result.minus2ll:.1f}, AIC = {result.aic:.1f}, BIC = {result.bic:.1f}")
for w in result.warnings:
    print(f"[!] {w}")

# EBE dataframe (eta per subject)
print(result.ebe.head())
```

### Diagnostic plots

```python
# 6-panel GOF + diagnostic plot
result.plot()

# HTML report
result.report("foce_i_report.html")
```

### 2-compartment model

```python
model_2cmt = PopPKModel(
    route="oral",
    fixed_effects={"CL_F": 4.0, "V1_F": 10.0, "Q": 5.0, "V2": 30.0, "ka": 1.5},
    omega_diag={"CL_F": 0.1, "V1_F": 0.1, "Q": 0.1, "V2": 0.1, "ka": 0.1},
    sigma_prop=0.15,
    sigma_add=0.0,
    n_cmt=2,
    omega_type="diagonal",
)
```

### CLI

```bash
openpkflow pop foce-i theoph.csv --route oral --cl 4.0 --v 30.0 --ka 1.5
```

---

## 2. SAEM estimation (PyMC tier)

SAEM requires PyMC (`pip install openpkflow[bayes]`). It uses the same
model definition and data format as FOCE-I.

```python
result_saem = run_saem(
    data,
    model,
    n_iterations=500,
    n_burn_in=200,
    alpha=0.75,
    seed=42,
)

print(result_saem.summary())
```

The SAEM result includes chain-mean parameter estimates, chain-based
standard errors, and a FOCE-I linearization -2LL computed at the final
estimates for model comparison.

### SAEM vs FOCE-I trade-off

| Aspect | FOCE-I | SAEM |
|--------|--------|------|
| Dependencies | Base install only | Requires PyMC (`[bayes]`) |
| Runtime | Seconds to minutes | Minutes (MCMC per iteration) |
| Convergence | L-BFGS-B outer loop | Stochastic approximation + MCMC |
| SEs | Delta-method via Hessian | Chain standard deviation |
| Best for | Quick fits, moderate data | Larger/richer datasets |

---

## 3. GOF analysis (from an existing fit)

If you have NONMEM output with PRED and IPRED columns, load it for
custom GOF plots:

```python
from openpkflow.pop import load_pop_csv, PopCSVConfig, GOFResult

config = PopCSVConfig(
    subject_col="ID",
    time_col="TIME",
    obs_col="DV",
    pred_col="PRED",
    ipred_col="IPRED",
)
df = load_pop_csv("pop_fit_output.csv", config=config)

gof = GOFResult.from_dataframe(df)
print(gof.summary())
# MPE, RMSE, rRMSE, R2 for both PRED and IPRED

gof.plot()          # returns base64 4-panel GOF figure
gof.report("gof_report.html")
```

The 4-panel GOF includes:

- OBS vs PRED (population predictions)
- OBS vs IPRED (individual predictions)
- IWRES vs TIME
- IWRES vs IPRED

---

## 4. Visual Predictive Check (VPC)

VPC uses your PK model to simulate replicate datasets and compute
percentile bands compared to observed data.

```python
from openpkflow.sim import OneCompartmentModel
from openpkflow.pop import simulate_vpc

model = OneCompartmentModel(route="oral", CL_F=4.0, Vz_F=30.0, ka=0.8)

vpc = simulate_vpc(
    obs_df=df,
    model=model,
    n_sims=200,
    seed=42,
)
vpc.report("vpc_report.html")
```

---

## 5. NONMEM-style dataset construction

Build a combined dose-plus-observation DataFrame compatible with
NONMEM/MONOLIX:

```python
from openpkflow.pop import create_nonmem_dataset
import pandas as pd

obs_df  = pd.read_csv("observations.csv")
dose_df = pd.read_csv("dosing.csv")

nm_df = create_nonmem_dataset(obs_df, dose_df)
nm_df.to_csv("nonmem_dataset.csv", index=False)
```

The output contains `EVID`, `MDV`, `AMT`, `TIME`, `DV` columns in
NONMEM convention.

---

## 6. Report export

```python
result.report("foce_i_report.html")
gof.report("gof_report.pdf")     # requires openpkflow[reports]
gof.report("gof_report.docx")
vpc.report("vpc_report.pdf")
```

---

## Regulatory notes

- Population PK results are exploratory. Regulatory submissions require
  validated software (NONMEM, Monolix, Phoenix NLME).
- FOCE-I and SAEM implementations are research-grade, validated against
  nlme reference values (Pinheiro & Bates 2000, Table 8.1) within 20%
  relative tolerance.
- Covariate estimation was removed in v2.3.0. Use Pharmpy or nlmixr2 for
  covariate selection, then OpenPKFlow for base model estimation.
