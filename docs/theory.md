# Theory Guide

Formula derivations for every core module in OpenPKFlow — intended for regulatory
reviewers, method validation, and teaching reference.

---

## NCA: Non-Compartmental Analysis

### Linear trapezoidal rule

$$
\text{AUC}_{\text{last}} = \sum_{i=0}^{n-2} \frac{C_i + C_{i+1}}{2} (t_{i+1} - t_i)
$$

Each interval is treated as a trapezoid. Exact for linear pharmacokinetics.

### Log-linear trapezoidal rule

For a declining interval $C_i > C_{i+1} > 0$:

$$
\int_{t_i}^{t_{i+1}} C(t)\,dt = \frac{C_i - C_{i+1}}{\ln(C_i / C_{i+1})} (t_{i+1} - t_i)
$$

Derived from $C(t) = C_i \cdot e^{-k(t-t_i)}$ with $k = \ln(C_i/C_{i+1})/(t_{i+1}-t_i)$.
When $C_i \leq 0$ or $C_i = C_{i+1}$, falls back to linear trapezoidal.

### Linear-up / log-down hybrid

$$
\text{AUC}_{\text{interval}} =
\begin{cases}
\frac{C_i + C_{i+1}}{2} \Delta t & \text{if } C_{i+1} \geq C_i \text{ (rising)} \\[4pt]
\frac{C_i - C_{i+1}}{\ln(C_i / C_{i+1})} \Delta t & \text{if } C_{i+1} < C_i \text{ and } C_{i+1} > 0 \text{ (declining)}
\end{cases}
$$

This is the WinNonlin/FDA default.

### Terminal elimination rate constant ($\lambda_z$)

BAR² (Best Adjusted R-squared) algorithm:

1. Identify all post-$C_{\max}$ positive-concentration points
2. Enumerate every contiguous terminal window of size $k \in [3, n_{\text{post}}]$ that includes the last point
3. For each window, fit $\ln(C) = \alpha + \lambda_z t$ via OLS
4. Reject windows with non-negative slope
5. Select the window maximising adjusted $R^2$; tie-break by more points, then longer time span
6. $\lambda_z = -\,\text{slope}$

### Derived NCA parameters

| Parameter | Formula | Notes |
|-----------|---------|-------|
| $t_{1/2}$ | $\ln(2) / \lambda_z$ | Terminal half-life |
| $\text{AUC}_{\inf}$ | $\text{AUC}_{\text{last}} + C_{\text{last}} / \lambda_z$ | Extrapolated AUC |
| $\%\text{AUC}_{\text{extrap}}$ | $(\text{AUC}_{\inf} - \text{AUC}_{\text{last}}) / \text{AUC}_{\inf} \times 100$ | FDA flag if $>20\%$ |
| $\text{CL}/F$ (oral) | $\text{Dose} / \text{AUC}_{\inf}$ | Apparent clearance |
| $V_z/F$ (oral) | $\text{Dose} / (\text{AUC}_{\inf} \cdot \lambda_z)$ | Apparent volume |
| $\text{CL}$ (IV) | $\text{Dose} / \text{AUC}_{\inf}$ | Absolute clearance |
| $V_z$ (IV) | $\text{Dose} / (\text{AUC}_{\inf} \cdot \lambda_z)$ | Absolute volume |
| $C_0$ (IV bolus) | $\exp(\text{intercept})$ | OLS of $\ln(C)$ on first 2 points |

### Steady-state NCA

$$
\begin{aligned}
C_{\text{avg}} &= \frac{\text{AUC}_{\tau}}{\tau} \\
\text{Fluctuation}\% &= \frac{C_{\max,ss} - C_{\min,ss}}{C_{\text{avg}}} \times 100 \\
\text{Swing} &= \frac{C_{\max,ss} - C_{\min,ss}}{C_{\min,ss}}
\end{aligned}
$$

### Urinary excretion

$$
\begin{aligned}
A_e(t) &= \sum_{i} V_{\text{urine},i} \cdot C_{\text{urine},i} \\
\text{CL}_r &= A_{e,\text{total}} / \text{AUC}_{\inf} \\
\%A_e &= A_{e,\text{total}} / \text{Dose} \times 100
\end{aligned}
$$

---

## PK Simulation: Analytical Solutions

All simulations use closed-form solutions (no numerical ODE integration). Superposition
is applied for multiple doses — valid only for **linear PK**.

### 1-compartment IV bolus

$$
C(t) = \frac{D}{V_z}\, e^{-k_e t}, \quad k_e = \frac{CL}{V_z}
$$

$C(0) = D/V_z$, mono-exponential decay.

### 1-compartment IV infusion

During infusion $(t \leq T)$:

$$
C(t) = \frac{R_0}{\text{CL}} \left(1 - e^{-k_e t}\right), \quad R_0 = D/T
$$

Post-infusion $(t > T)$:

$$
C(t) = \frac{R_0}{\text{CL}} \left(1 - e^{-k_e T}\right) e^{-k_e (t - T)}
$$

### 1-compartment oral (Bateman equation)

$$
C(t) = \frac{D \cdot k_a}{V_z/F \cdot (k_a - k_e)} \left(e^{-k_e t} - e^{-k_a t}\right)
$$

Peak time:

$$
t_{\max} = \frac{\ln(k_a / k_e)}{k_a - k_e}
$$

**Flip-flop case** $(k_a = k_e)$:

$$
C(t) = \frac{D \cdot k}{V_z/F} \cdot t \cdot e^{-k t}
$$

### 2-compartment IV bolus

$$
C(t) = A e^{-\alpha t} + B e^{-\beta t}
$$

where $\alpha > \beta$, $A + B = D/V_1$ (the initial condition), and:

$$
\begin{aligned}
\alpha, \beta &= \frac{1}{2}\left[(k_{10} + k_{12} + k_{21}) \pm \sqrt{(k_{10} + k_{12} + k_{21})^2 - 4k_{10}k_{21}}\right] \\
A &= \frac{D}{V_1} \cdot \frac{\alpha - k_{21}}{\alpha - \beta} \\
B &= \frac{D}{V_1} \cdot \frac{k_{21} - \beta}{\alpha - \beta} \\
k_{10} &= \frac{CL}{V_1}, \quad k_{12} = \frac{Q}{V_1}, \quad k_{21} = \frac{Q}{V_2}
\end{aligned}
$$

### 2-compartment oral

$$
C(t) = A_1 e^{-\alpha t} + A_2 e^{-\beta t} + A_3 e^{-k_a t}
$$

with $A_1 + A_2 + A_3 = 0$ (ensuring $C(0) = 0$).

### Superposition (repeated dosing)

For a linear system, concentration after $N$ doses is the sum of individual dose
contributions shifted by their administration times:

$$
C_{\text{total}}(t) = \sum_{i=1}^{N} C_{\text{unit}}(t - t_{\text{dose},i}) \cdot \text{Dose}_i / D_{\text{unit}}
$$

This principle is used for all repeated-dose simulations.

---

## Dissolution Similarity

### f2 similarity factor

$$
f_2 = 50 \cdot \log_{10}\left(\frac{100}{\sqrt{1 + \frac{1}{n}\sum_{i=1}^{n}(R_i - T_i)^2}}\right)
$$

- $f_2 = 100$ when profiles are identical
- $f_2 \geq 50$ indicates similarity (FDA 1997)
- Time points after both profiles exceed $85\%$ release are trimmed (regulatory method)

### f1 difference factor

$$
f_1 = \frac{\sum_{i=1}^{n} |R_i - T_i|}{\sum_{i=1}^{n} R_i} \times 100
$$

- $f_1 = 0$ when profiles are identical
- $f_1 \leq 15$ indicates similarity

### Bootstrap f2

When $n < 12$ vessels, the bootstrap 90\% CI for $f_2$ is computed:

1. Bootstrap-resample the vessel-level data $B = 2000$ times
2. Compute $f_2$ for each resample
3. Report the 90\% CI; similarity concluded if CI lower bound $\geq 50$

Reference: Shah et al. (1998), *Pharm Res* 15(6):889-896.

### Dissolution models

| Model | Equation | Parameters |
|-------|----------|------------|
| Zero-order | $Q(t) = k_0 t$ | $k_0$ |
| First-order | $Q(t) = 100(1 - e^{-k_1 t})$ | $k_1$ |
| Higuchi | $Q(t) = k_H \sqrt{t}$ | $k_H$ |
| Korsmeyer-Peppas | $Q(t) = k t^n$ | $k, n$ |
| Weibull | $Q(t) = 100(1 - e^{-(t/\beta)^\alpha})$ | $\alpha, \beta$ |

Models are fitted via `scipy.optimize.curve_fit` (NLS) and ranked by AICc.

Reference: Costa & Lobo (2001), *Eur J Pharm Sci* 13(2):123-133.

---

## IVIVC: In Vitro-In Vivo Correlation

### Wagner-Nelson deconvolution

For a 1-compartment model with first-order elimination:

$$
F_a(t) = \frac{C(t) + k_e \cdot \text{AUC}_{0\to t}}{k_e \cdot \text{AUC}_{0\to\infty}}
$$

- $F_a(t)$ is the fraction absorbed up to time $t$
- Requires only $k_e$ (from terminal phase) and plasma concentrations
- Does not require a separate IV dose

Reference: Wagner & Nelson (1963), *J Pharm Sci* 52(6):610-611.

### Loo-Riegelman deconvolution

For a 2-compartment model:

$$
F_a(t) = \frac{C_p(t) + k_{10} \cdot \text{AUC}_{0\to t} + A_{p,t}/V_1}{k_{10} \cdot \text{AUC}_{0\to\infty}}
$$

where $A_{p,t}$ is the amount in the peripheral compartment at time $t$, computed recursively:

$$
A_{p}(t_{i+1}) = A_{p}(t_i) \cdot e^{-k_{21}\Delta t} + \frac{C_p(t_i) \cdot Q \cdot (1 - e^{-k_{21}\Delta t})}{k_{21}} + C_p(t_{i+1}) \cdot V_2 - \frac{C_p(t_i) \cdot V_2 \cdot k_{21} \cdot (1 - e^{-k_{21}\Delta t})}{k_{21}}
$$

Requires micro-rate constants $k_{10}, k_{12}, k_{21}$ from a separate IV study.

Reference: Loo & Riegelman (1968), *J Pharm Sci* 57(6):918-928.

### Numerical convolution

Predicted concentration from dissolution:

$$
C_{\text{pred}}(t) = \sum_{i=1}^{m} \Delta F_{\text{diss},i} \cdot C_{\text{IR}}(t - t_i)
$$

where $C_{\text{IR}}$ is the unit impulse response (IR formulation profile) and
$\Delta F_{\text{diss},i}$ is the incremental fraction dissolved.

### Predictability (%PE)

$$
\%\text{PE}_{AUC} = \frac{\text{AUC}_{\text{obs}} - \text{AUC}_{\text{pred}}}{\text{AUC}_{\text{obs}}} \times 100
$$

FDA IVIVC acceptance criteria:
- Mean $\%$PE for $C_{\max}$ and AUC $\leq 10\%$
- Individual $\%$PE for $C_{\max}$ $\leq 15\%$

Reference: FDA Guidance IVIVC (1997).

### Levy plot

Linear regression of $F_{a,\text{in-vivo}}$ vs $F_{\text{diss, in-vitro}}$:

$$
F_{a,\text{in-vivo}} = a + b \cdot F_{\text{diss, in-vitro}}
$$

$R^2$ measures the strength of the IVIVC. A perfect 1:1 relationship gives
$R^2 = 1$, slope $= 1$, intercept $= 0$.

---

## Bioequivalence (TOST)

### Two one-sided tests

For paired log-transform data:

1. Compute log-differences: $d_i = \ln(T_i) - \ln(R_i)$
2. Mean log-difference: $\bar{d} = \frac{1}{n}\sum d_i$
3. Geometric mean ratio: $\text{GMR} = e^{\bar{d}}$
4. Intra-subject variance: $s^2 = \frac{1}{n-1}\sum(d_i - \bar{d})^2$
5. Intra-subject CV: $\text{CV}_{\text{intra}}\% = 100 \cdot \sqrt{e^{s^2} - 1}$
6. 90\% confidence interval for GMR:

$$
\text{CI}_{90\%} = \exp\left(\bar{d} \pm t_{0.05, n-1} \cdot \frac{s}{\sqrt{n}}\right)
$$

**Decision rule:** Bioequivalent if $\text{CI}_{\text{lower}} \geq 0.80$ and
$\text{CI}_{\text{upper}} \leq 1.25$.

Reference: Schuirmann (1987), *J Pharmacokinet Biopharm* 15(6):657-680.

### Power of TOST ($1 - \beta$)

Using the non-central $t$ distribution:

$$
\text{power} = P\left(t_{n-2}(\delta) > t_{0.05, n-2}\right) - P\left(t_{n-2}(\delta) < -t_{0.05, n-2}\right)
$$

where:

$$
\delta = \frac{\ln(\text{GMR})}{s / \sqrt{n}}
$$

This is the exact Phillips non-central $t$ method.

Reference: Phillips (1990), *J Pharmacokinet Biopharm* 18(2):137-144.

### Sample size

Sequential search for the smallest even $n$ such that power $\geq$ target (default 0.80).

Reference: Diletti et al. (1991), *Int J Clin Pharmacol Ther Toxicol* 29(1):1-8.

---

## Population PK

### Model structure

$$
C_{ij} = f(\phi_i, t_{ij})
$$

where $\phi_i$ are individual parameters:

$$
\phi_i = \theta_{\text{pop}} \cdot \exp(\eta_i), \quad \eta_i \sim \mathcal{N}(0, \Omega)
$$

Residual error model (combined):

$$
y_{ij} = C_{ij} + \epsilon_{ij}, \quad \epsilon_{ij} \sim \mathcal{N}(0, \sigma_{\text{prop}}^2 \cdot C_{ij}^2 + \sigma_{\text{add}}^2)
$$

### FOCE-I objective function

The first-order conditional estimation with interaction (-2 log-likelihood):

$$
-2\ell(\theta, \Omega, \Sigma) = \sum_{i=1}^{N} \left[ n_i \ln(2\pi) + \ln|V_i| + (y_i - f_i - G_i\hat{\eta}_i)^T V_i^{-1}(y_i - f_i - G_i\hat{\eta}_i) + \hat{\eta}_i^T \Omega^{-1} \hat{\eta}_i + \ln|\Omega| \right]
$$

where:

- $V_i = G_i \Omega G_i^T + \Sigma_i$ (linearised marginal variance)
- $G_i = \partial f_i / \partial \eta_i^T$ (Jacobian of predictions w.r.t. random effects)
- $\hat{\eta}_i = \arg\min_\eta \left[ (y_i - f_i(\eta))^T \Sigma_i^{-1}(y_i - f_i(\eta)) + \eta^T \Omega^{-1} \eta \right]$ (empirical Bayes estimate)

**Inner loop:** Per-subject L-BFGS-B optimisation for $\hat{\eta}_i$ (EBEs)
**Outer loop:** L-BFGS-B over $\theta_{\text{pop}}, \Omega, \Sigma$

Reference: Lindstrom & Bates (1990), *Biometrics* 46:673-687.

### SAEM algorithm

**Simulation (S-step):** Sample $\eta_i^{(k)}$ from the conditional distribution
$p(\eta_i \mid y_i, \theta^{(k-1)})$ using Metropolis MCMC.

**Stochastic Approximation (SA-step):**

$$
s_k = s_{k-1} + \gamma_k \left(S(\eta^{(k)}) - s_{k-1}\right)
$$

where $\gamma_k = 1/k^\alpha$ (Robbins-Monro gain, $\alpha \in (0.5, 1]$).

**Maximisation (M-step):** Analytical update of population parameters from
sufficient statistics $s_k$.

Reference: Delyon, Lavielle & Moulines (1999), *Ann Stat* 27(1):94-128.

### Information criteria

$$
\begin{aligned}
\text{AIC} &= -2\ell + 2p \\
\text{BIC} &= -2\ell + p \ln(N_{\text{obs}})
\end{aligned}
$$

where $p$ is the total number of estimated parameters ($\theta_{\text{pop}} + \Omega + \Sigma$).

### EBE shrinkage

$$
\text{Shrinkage}_k = 1 - \frac{\text{Var}(\hat{\eta}_{k,i})}{\omega_k^2}
$$

- 0\% = no shrinkage (data dominates)
- 100\% = complete shrinkage (prior dominates)
- High shrinkage ($> 30\%$) indicates the data contains little information
  about that parameter

Reference: Savic & Karlsson (2009), *AAPS J* 11(3):558-569.

---

## Bayesian PK

### MAP estimation

Maximises the log-posterior:

$$
\hat{\theta}_{\text{MAP}} = \arg\max_\theta \left[\ln p(\theta) + \ln p(y \mid \theta)\right]
$$

With log-normal priors $\theta_k \sim \text{LogNormal}(\mu_k, \sigma_k^2)$:

$$
\ln p(\theta) = -\sum_k \left[\frac{(\ln\theta_k - \mu_k)^2}{2\sigma_k^2} + \ln(\theta_k) + \ln(\sigma_k) + \frac{1}{2}\ln(2\pi)\right]
$$

Optimised via L-BFGS-B in log-space. Hessian at the mode gives asymptotic
standard errors (inverse Fisher information).

Reference: Sheiner & Beal (1982), *J Pharm Sci* 71:1344-1348.

### Full Bayesian (MCMC)

Posterior sampling via PyMC NUTS:

$$
p(\theta \mid y) \propto p(\theta) \cdot p(y \mid \theta)
$$

Outputs include 95\% credible intervals and effective sample size (ESS).

### Bayesian BE

Posterior probability of bioequivalence:

$$
P(\text{BE} \mid y) = P(0.80 \leq \text{GMR} \leq 1.25 \mid y)
$$

Bayesian and frequentist GMR estimates are reported side-by-side.

Reference: Grieve (1985), *Biometrics* 41:979-990.

---

## References

1. FDA Guidance: Dissolution Testing of Immediate Release Solid Oral Dosage Forms (1997)
2. FDA Guidance: Extended Release Oral Dosage Forms — IVIVC (1997)
3. FDA Guidance: Statistical Approaches to Establishing Bioequivalence (2001)
4. FDA Guidance: BA/BE Studies for Orally Administered Drug Products (2003)
5. Schuirmann (1987), *J Pharmacokinet Biopharm* 15(6):657-680
6. Phillips (1990), *J Pharmacokinet Biopharm* 18(2):137-144
7. Gibaldi & Perrier (1982), *Pharmacokinetics*, 2nd ed., Marcel Dekker
8. Rowland & Tozer (2011), *Clinical Pharmacokinetics*, 4th ed.
9. Wagner & Nelson (1963), *J Pharm Sci* 52(6):610-611
10. Loo & Riegelman (1968), *J Pharm Sci* 57(6):918-928
11. Lindstrom & Bates (1990), *Biometrics* 46:673-687
12. Delyon, Lavielle & Moulines (1999), *Ann Stat* 27(1):94-128
13. Sheiner & Beal (1982), *J Pharm Sci* 71:1344-1348
14. Savic & Karlsson (2009), *AAPS J* 11(3):558-569
15. Costa & Lobo (2001), *Eur J Pharm Sci* 13(2):123-133
16. Shah et al. (1998), *Pharm Res* 15(6):889-896
17. Pinheiro & Bates (2000), *Mixed-Effects Models in S and S-PLUS*, Springer
18. Grieve (1985), *Biometrics* 41:979-990
