# Tutorial: IVIVC Level A

This tutorial walks through a complete In Vitro-In Vivo Correlation (Level A)
analysis: deconvolution, Levy plot, convolution prediction, and FDA predictability
assessment using OpenPKFlow.

---

## 1. Wagner-Nelson deconvolution

Given oral plasma concentration data and either a known elimination rate
constant (`kel`) or IV bolus unit impulse response (UIR) data, Wagner-Nelson
computes the cumulative fraction absorbed over time.

```python
from openpkflow.ivivc import wagner_nelson

iv_times = [0.0, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0]
iv_concs = [48.2, 25.5, 19.0, 10.2, 3.3, 1.1, 0.4, 0.1]
oral_times = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
oral_concs = [0.0, 4.4, 9.8, 13.5, 16.6, 18.2, 16.1, 9.2, 4.8]

fa = wagner_nelson(
    oral_times,
    oral_concs,
    iv_unit_impulse_times=iv_times,
    iv_unit_impulse_concs=iv_concs,
)

print("Fraction absorbed:")
for t, f in zip(oral_times, fa):
    print(f"  t={t:.1f} h: F_a={f:.3f}")
```

If you know `kel` directly (e.g. from an NCA analysis), pass it instead of UIR data:

```python
fa = wagner_nelson(oral_times, oral_concs, kel=0.15)
```

---

## 2. Loo-Riegelman deconvolution (2-compartment)

For drugs with distribution-phase kinetics, use Loo-Riegelman with all three
microconstants:

```python
from openpkflow.ivivc import loo_riegelman

fa_2cmt = loo_riegelman(
    oral_times,
    oral_concs,
    kel=0.25,
    k12=0.40,
    k21=0.30,
)
```

---

## 3. Levy plot: correlating in vitro and in vivo

Match dissolution time points to the fraction absorbed curve and build a
Levy plot with linear regression:

```python
from openpkflow.ivivc import levy_plot_data

diss_times = [10, 20, 30, 45, 60, 90, 120]
diss_pct = [12.0, 27.0, 42.0, 57.0, 68.0, 82.0, 93.0]
diss_frac = [p / 100.0 for p in diss_pct]

import numpy as np
fa_interp = np.interp(diss_times, oral_times, fa, left=0.0, right=min(fa[-1], 1.0))

levy = levy_plot_data(diss_times, diss_frac, fa_interp)
print(f"Slope: {levy['slope']:.3f}, R-squared: {levy['r_squared']:.3f}")
```

A slope near 1.0 with high R-squared indicates a strong IVIVC correlation.

---

## 4. Convolution prediction

Predict the in vivo plasma profile from dissolution data by convolving the
dissolution input rate with the IV unit impulse response:

```python
from openpkflow.ivivc import convolution_predict

pred_times, pred_concs = convolution_predict(
    diss_times,
    diss_pct,
    iv_unit_impulse_times=iv_times,
    iv_unit_impulse_concs=iv_concs,
    dose_diss=100.0,
    dose_iv=100.0,
)

print(f"Predicted Cmax: {max(pred_concs):.2f}")
```

For relative prediction (dose-normalised), omit `dose_diss` and `dose_iv`.

---

## 5. Predictability assessment

Per FDA 1997 guidance, assess how well the IVIVC predicts Cmax and AUCinf:

```python
from openpkflow.ivivc import ivivc_predictability

obs_cmax = max(oral_concs)
pred_cmax = max(pred_concs)
obs_auc = 120.0   # from NCA analysis on oral data
pred_auc = 115.0  # AUCinf from predicted profile

pp = ivivc_predictability(obs_cmax, pred_cmax, obs_auc, pred_auc)

print(f"%PE Cmax: {pp['%PE_Cmax']:.1f}%  (pass: {pp['passes_cmax']})")
print(f"%PE AUC:  {pp['%PE_AUC']:.1f}%  (pass: {pp['passes_auc']})")
print(f"Mean abs %PE: {pp['mean_abs_%PE']:.1f}%  (pass: {pp['passes_mean']})")
print(f"Overall: {'PASS' if pp['overall_pass'] else 'FAIL'}")
```

Pass criteria: %PE Cmax <= 15%, %PE AUC <= 15%, mean abs %PE <= 10%.

---

## 6. Complete workflow with IVIVCStudy

`IVIVCStudy` orchestrates all steps in one call:

```python
from openpkflow.ivivc import IVIVCStudy

study = IVIVCStudy(
    in_vivo_times=oral_times,
    in_vivo_concs=oral_concs,
    dissolution_times=diss_times,
    dissolution_pct=diss_pct,
    iv_uir_times=iv_times,
    iv_uir_concs=iv_concs,
    method="wagner_nelson",
    dose_diss=100.0,
    dose_iv=100.0,
    study_label="Formulation_A_LevelA",
)

result = study.analyze()

result.summary()        # text summary to stdout
result.plot(show=True)  # 4-panel figure
result.report("ivivc_report.html")  # HTML report with embedded figures
```

For Loo-Riegelman, add the microconstants:

```python
study = IVIVCStudy(
    ...,
    method="loo_riegelman",
    kel=0.25, k12=0.40, k21=0.30,
)
```

---

## 7. Report export

```python
result.report("ivivc_report.html")   # HTML
result.report("ivivc_report.md")     # Markdown
result.report("ivivc_report.pdf")    # requires openpkflow[reports]
result.report("ivivc_report.docx")   # requires openpkflow[reports]
```

---

## FDA regulatory notes

- IVIVC Level A requires a deconvolution-to-convolution workflow: fraction
  absorbed is derived from in vivo data, correlated to in vitro dissolution
  via a Levy plot, and then used to predict the plasma profile.
- The Levy plot should span the 0.05-0.95 fraction range where possible.
- Predictability requires at least one internal validation formulation
  (preferably two or more).
- F_a must be less than or equal to F_d at all matched time points for a
  valid IVIVC.
