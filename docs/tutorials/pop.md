# Tutorial: Population PK Diagnostics

This tutorial covers goodness-of-fit (GOF) plots, visual predictive checks (VPC),
and NONMEM-style dataset construction using `openpkflow.pop`.

!!! note
    These tools support diagnostics for an existing popPK model fit. They do not
    perform NLME parameter estimation. Bring your own PRED/IPRED/IWRES columns.

---

## 1. Load a population dataset

Your CSV should have columns: `ID`, `TIME`, `DV`, `PRED`, `IPRED`.

```python
from openpkflow.pop import load_pop_csv, PopCSVConfig

config = PopCSVConfig(
    subject_col="ID",
    time_col="TIME",
    obs_col="DV",
    pred_col="PRED",
    ipred_col="IPRED",
)
df = load_pop_csv("pop_fit_output.csv", config=config)
```

---

## 2. GOF analysis

```python
from openpkflow.pop import GOFResult, compute_iwres, obs_pred_metrics

gof = GOFResult.from_dataframe(df)
print(gof.summary())
# MPE, RMSE, rRMSE, R2 for both PRED and IPRED

gof.plot()        # returns base64 4-panel GOF figure
gof.report("gof_report.html")
```

The 4-panel GOF includes:

- OBS vs PRED (population predictions)
- OBS vs IPRED (individual predictions)
- IWRES vs TIME
- IWRES vs IPRED

---

## 3. Visual Predictive Check (VPC)

VPC requires a simulation function. OpenPKFlow uses your PK model to simulate
replicate datasets and computes percentile bands.

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

## 4. NONMEM-style dataset

Build a combined dose-plus-observation DataFrame compatible with NONMEM/MONOLIX:

```python
from openpkflow.pop import create_nonmem_dataset
import pandas as pd

obs_df  = pd.read_csv("observations.csv")
dose_df = pd.read_csv("dosing.csv")

nm_df = create_nonmem_dataset(obs_df, dose_df)
nm_df.to_csv("nonmem_dataset.csv", index=False)
```

The output contains `EVID`, `MDV`, `AMT`, `TIME`, `DV` columns in NONMEM convention.

---

## 5. Export

```python
gof.report("gof_report.pdf")    # requires openpkflow[reports]
gof.report("gof_report.docx")
vpc.report("vpc_report.pdf")
```
