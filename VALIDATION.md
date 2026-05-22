# Validation Documentation

This document maps OpenPKFlow test cases to their regulatory guidance sources and published references.

All pharmacokinetic calculations are validated against FDA/EMA guidance documents, peer-reviewed publications, and established pharmacokinetic textbooks.

---

## Regulatory Guidance References

### FDA Guidance Documents

| Guidance | Year | Modules | Test Files |
|----------|------|---------|------------|
| [Dissolution Testing of Immediate Release Solid Oral Dosage Forms](https://www.fda.gov/media/71513/download) | 1997 | dissolution | `tests/dissolution/test_similarity.py` |
| [Bioavailability and Bioequivalence Studies for Orally Administered Drug Products](https://www.fda.gov/media/71513/download) | 2003 | nca, be | `tests/nca/test_methods.py`, `tests/be/test_methods.py` |
| [Statistical Approaches to Establishing Bioequivalence](https://www.fda.gov/media/71513/download) | 2001 | be | `tests/be/test_methods.py` |
| [Waiver of In Vivo Bioavailability and Bioequivalence Studies](https://www.fda.gov/media/71513/download) | 2021 | dissolution | `tests/dissolution/test_similarity.py` |

### EMA Guidelines

| Guideline | Year | Modules | Test Files |
|-----------|------|---------|------------|
| [Guideline on the Investigation of Bioequivalence](https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-investigation-bioequivalence-rev1_en.pdf) | 2010 | be | `tests/be/test_methods.py` |
| [ICH Q6A: Specifications](https://database.ich.org/sites/default/files/Q6A%20Guideline.pdf) | 1999 | dissolution | `tests/dissolution/test_similarity.py` |

---

## Published References

### Pharmacokinetics Textbooks

| Reference | Modules | Test Files |
|-----------|---------|------------|
| Gibaldi M, Perrier D (1982). *Pharmacokinetics*, 2nd ed. Marcel Dekker | sim, nca | `tests/sim/test_methods.py`, `tests/nca/test_methods.py` |
| Rowland M, Tozer TN (2011). *Clinical Pharmacokinetics and Pharmacodynamics*, 4th ed. | nca, be | `tests/nca/test_methods.py`, `tests/validation/test_nca_validation.py` |
| Shargel L, Yu A (2015). *Applied Biopharmaceutics & Pharmacokinetics*, 7th ed. | dissolution, nca | `tests/dissolution/test_models.py`, `tests/nca/test_methods.py` |

### Peer-Reviewed Papers

| Paper | DOI | Modules | Test Files |
|-------|-----|---------|------------|
| Schuirmann DJ (1987). A comparison of the Two One-Sided Tests Procedure and the Power Approach for assessing the equivalence of average bioavailability. *J Pharmacokinet Biopharm* 15(6):657-680 | [10.1007/BF01068419](https://doi.org/10.1007/BF01068419) | be | `tests/be/test_methods.py` |
| Shah VP et al. (1998). In vitro dissolution profile comparison—statistics and analysis of the similarity factor, f2. *Pharm Res* 15(6):889-896 | [10.1023/A:1011976615750](https://doi.org/10.1023/A:1011976615750) | dissolution | `tests/dissolution/test_bootstrap.py` |
| Costa P, Lobo JMS (2001). Modeling and comparison of dissolution profiles. *Eur J Pharm Sci* 13(2):123-133 | [10.1016/S0928-0987(01)00095-1](https://doi.org/10.1016/S0928-0987(01)00095-1) | dissolution | `tests/dissolution/test_models.py` |
| Davit BM et al. (2013). Implementing the f2 similarity factor in bioequivalence. *Pharm Res* 30(11):2772-2777 | [10.1007/s11095-013-1099-8](https://doi.org/10.1007/s11095-013-1099-8) | dissolution | `tests/dissolution/test_bootstrap.py` |
| Moore JW, Flanner HH (1996). Mathematical comparison of dissolution profiles. *Pharm Technol* 20(6):64-74 | N/A | dissolution | `tests/dissolution/test_similarity.py` |

---

## Module-Specific Validation

### Dissolution Module

#### f1 and f2 Similarity Factors

**Regulatory Basis:**
- FDA Guidance (1997): f1 ≤ 15 and f2 ≥ 50 indicate similarity
- EMA Guideline (2010): f2 calculation methodology
- Moore & Flanner (1996): Original f1/f2 equations

**Validation Tests:**
- `tests/dissolution/test_similarity.py`
  - f1 = 10.0 exactly when test is uniform 10% reduction (FDA 1997)
  - f2 ≈ 50 when profiles differ by 10% at every timepoint (FDA 1997)
  - Identical profiles: f2 = 100, f1 = 0 (degenerate case)
  - Regulatory method trims timepoints where both > 85% dissolved (FDA 1997)

#### Bootstrap f2

**Regulatory Basis:**
- Shah VP et al. (1998): Bootstrap methodology for small sample sizes
- Davit BM et al. (2013): f2 bootstrap confidence intervals

**Validation Tests:**
- `tests/dissolution/test_bootstrap.py`
  - Similar profiles: CI lower bound ≥ 50
  - Dissimilar profiles: CI lower bound < 50
  - 95% CI wider than 90% CI (statistical property)
  - Reproducibility with fixed seed

#### Dissolution Model Fitting

**Regulatory Basis:**
- Costa P, Lobo JMS (2001): Model comparison methodology
- FDA Guidance (1997): Model-based dissolution comparison

**Validation Tests:**
- `tests/dissolution/test_models.py`
  - AICc ranking: best model has lowest AICc
  - Weibull, Korsmeyer-Peppas, Higuchi, First-order, Zero-order models
  - R² reporting (not used for selection, misleading for nonlinear models)

---

### NCA Module

#### AUC Calculations

**Regulatory Basis:**
- FDA Guidance (2003): AUClast, AUCinf calculation methodology
- Gibaldi & Perrier (1982): Trapezoidal rule equations

**Validation Tests:**
- `tests/nca/test_methods.py`
  - Linear trapezoidal: exact for linear concentration-time profiles
  - Log trapezoidal: exact for exponential decay phases
  - Linear-up/log-down: linear for absorption, log for elimination
  - AUCinf = AUClast + Clast/λz (FDA 2003)

#### Clearance and Volume Parameters

**Regulatory Basis:**
- Gibaldi & Perrier (1982): CL = Dose/AUCinf, Vz = Dose/(AUCinf × λz)
- Rowland & Tozer (2011): CL_F vs CL distinction (oral vs IV)

**Validation Tests:**
- `tests/validation/test_nca_validation.py`
  - IV bolus: NCA CL recovered within 2% of true CL
  - IV bolus: NCA Vz recovered within 2% of true Vz
  - IV bolus: NCA t½ recovered within 2% of true t½
  - Oral: NCA CL_F recovered within 5% of true CL_F
  - AUCinf = Dose/CL (exact identity, Rowland & Tozer Eq. 3-1)

#### Lambda-z Estimation

**Regulatory Basis:**
- FDA Guidance (2003): Terminal elimination rate constant
- PKNCA R package: BAR² adjusted R² algorithm

**Validation Tests:**
- `tests/nca/test_methods.py`
  - Auto-selection: chooses window with highest adjusted R²
  - At least 3 points required (regulatory standard)
  - Half-life = ln(2)/λz (Gibaldi & Perrier Eq. 1-4)

---

### Bioequivalence Module

#### Two One-Sided Tests (TOST)

**Regulatory Basis:**
- Schuirmann DJ (1987): TOST procedure for bioequivalence
- FDA Guidance (2001): Statistical approaches to BE
- EMA Guideline (2010): 80-125% acceptance range

**Validation Tests:**
- `tests/be/test_methods.py`
  - Identical profiles: GMR = 1.0 (degenerate case)
  - Known CI width: manual calculation for n=4
  - 80-125% acceptance window: GMR = 0.70 fails, GMR = 0.90 passes
  - NTI products: 90-111.11% narrower limits (EMA 2010)
  - Symmetry: GMR(T,R) = 1/GMR(R,T)

#### Intra-Subject CV

**Regulatory Basis:**
- FDA Guidance (2001): CV% calculation from within-subject variance
- EMA Guideline (2010): CV reporting requirements

**Validation Tests:**
- `tests/be/test_methods.py`
  - Zero variability: CV = 0%
  - Positive variability: CV > 0%
  - CV% stored in results

---

### Simulation Module

#### 1-Compartment IV Bolus

**Regulatory Basis:**
- Gibaldi & Perrier (1982): Eq. 1-2, C(t) = (D/Vz) × exp(-k×t)
- Rowland & Tozer (2011): AUCinf = D/CL (Eq. 3-1)

**Validation Tests:**
- `tests/validation/test_sim_validation.py`
  - C(t½) = C(0)/2 (half-life definition)
  - AUCinf = D/CL within 0.5% (numerical integration)
  - AUC(0 to 2×t½)/AUCinf = 0.75 (exact)

#### 1-Compartment Oral (Bateman Equation)

**Regulatory Basis:**
- Gibaldi & Perrier (1982): Eq. 1-13, Bateman function
- Shargel & Yu (2015): Tmax = ln(ka/k)/(ka-k)

**Validation Tests:**
- `tests/validation/test_sim_validation.py`
  - Tmax formula: ln(ka/k)/(ka-k) within 0.5%
  - AUCinf = D/CL_F within 0.5%

#### 2-Compartment IV Bolus

**Regulatory Basis:**
- Gibaldi & Perrier (1982): Eq. 3-1, biexponential decay
- Rowland & Tozer (2011): C(0) = D/V1

**Validation Tests:**
- `tests/validation/test_sim_validation.py`
  - AUCinf = D/CL within 1%
  - C(0) = D/V1 within 0.001%

#### 2-Compartment IV Infusion

**Regulatory Basis:**
- Gibaldi & Perrier (1982): Eqs. 3-28 to 3-30
- Rowland & Tozer (2011): AUCinf independent of infusion duration

**Validation Tests:**
- `tests/validation/test_sim_validation.py`
  - AUCinf = D/CL within 1%
  - AUCinf independent of infusion duration (linear PK property)

---

### Population PK Diagnostics Module

#### Goodness-of-Fit Plots

**Regulatory Basis:**
- FDA Guidance (2013): Population pharmacokinetics
- Bonate PL (2011): *Pharmacokinetic-Pharmacodynamic Modeling and Simulation*

**Validation Tests:**
- `tests/pop/test_gof.py`
  - OBS vs PRED plot generation
  - OBS vs IPRED plot generation
  - CWRES vs TIME/IPRED plots
  - 4-panel GOF figure generation

#### Visual Predictive Check (VPC)

**Regulatory Basis:**
- Karlsson MO, Holford N (2008): VPC methodology
- FDA Guidance (2013): Model evaluation

**Validation Tests:**
- `tests/pop/test_vpc.py`
  - Percentile bands: 5th, 50th, 95th
  - Observed data overlay
  - Reproducibility with fixed seed

---

### ML Surrogate Module (Experimental)

#### Physics-Informed Neural Network

**Status:** Experimental - not validated against regulatory standards

**Validation Tests:**
- `tests/ml/test_surrogate.py`
  - R² ≥ 0.95 vs analytical solutions (internal validation)
  - Not recommended for regulatory submissions

---

## Validation Methodology

### Test Case Design

1. **Degenerate Cases:** Edge cases with known exact answers (e.g., identical profiles, zero variability)
2. **Regulatory Examples:** Numerical examples from FDA/EMA guidance documents
3. **Textbook Validation:** Equations and worked examples from standard pharmacokinetics textbooks
4. **Cross-Validation:** NCA vs simulation round-trip tests
5. **Statistical Properties:** Confidence interval width, reproducibility, symmetry

### Tolerance Criteria

| Parameter | Tolerance | Rationale |
|-----------|-----------|-----------|
| f1, f2 | ±0.01 | Exact calculation |
| AUC (linear) | ±0.01% | Numerical integration |
| AUCinf | ±2% | Depends on λz estimation |
| CL, Vz | ±2% (IV), ±5% (oral) | IV more precise, oral includes absorption variability |
| t½ | ±2% | Depends on λz estimation |
| BE CI width | ±0.001 | Statistical calculation |

### Continuous Validation

- **CI/CD:** All tests run on every commit (GitHub Actions)
- **Coverage:** pytest-cov measures test coverage
- **Benchmarking:** pytest-benchmark tracks performance regressions
- **Version Compatibility:** Tested on Python 3.10, 3.11, 3.12

---

## Limitations and Disclaimers

1. **Open-Source Tool:** OpenPKFlow is an open-source research tool. Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.

2. **Not a Replacement:** This tool does not replace expert regulatory judgment or validated commercial platforms (WinNonlin, Phoenix, SAS).

3. **Experimental Modules:** ML surrogate module is experimental and not validated against regulatory standards.

4. **Validation Scope:** Validation tests cover mathematical correctness and regulatory compliance, but do not cover all edge cases or real-world data quality issues.

5. **Guidance Updates:** FDA/EMA guidance documents are periodically updated. Users should verify that their analyses comply with the most current guidance.

---

## How to Cite Validation Sources

When using OpenPKFlow for regulatory submissions, cite the original sources:

```
FDA (1997). Guidance for Industry: Dissolution Testing of Immediate Release
Solid Oral Dosage Forms. CDER, U.S. Food and Drug Administration.

Gibaldi M, Perrier D (1982). Pharmacokinetics, 2nd ed. Marcel Dekker, New York.

Schuirmann DJ (1987). A comparison of the Two One-Sided Tests Procedure and
the Power Approach for assessing the equivalence of average bioavailability.
J Pharmacokinet Biopharm 15(6):657-680. DOI: 10.1007/BF01068419
```

---

## Contributing Validation Tests

When adding new tests, follow this format:

```python
def test_function_name():
    """Test description.

    Reference:
    - FDA Guidance (Year): Section/page
    - Gibaldi & Perrier (1982): Equation X-Y
    - DOI: 10.xxxx/xxxxx
    """
    # Test implementation
    assert result == pytest.approx(expected, tolerance)
```

All validation tests should include:
1. Clear reference to regulatory guidance or published source
2. Hand-calculable expected values where possible
3. Appropriate tolerance based on numerical precision requirements
4. Documentation in this VALIDATION.md file

---

**Last Updated:** 2026-05-22
**Maintainer:** Priyam Thakar (priyamthakar1@gmail.com)
