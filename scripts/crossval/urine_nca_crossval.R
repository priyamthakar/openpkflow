#!/usr/bin/env Rscript
#
# urine_nca_crossval.R
#
# Independent R implementation of urinary NCA formulas to cross-validate
# openpkflow's nca/methods.py cumulative_urinary_excretion(), renal_clearance(),
# and percent_excreted().
#
# Strategy: implement each formula directly in R (simple math, no packages).
# Use a synthetic dataset where true values are known analytically from the
# 1-compartment IV bolus renal excretion model.
#
# Model:
#   Plasma: C(t) = (D/V) * exp(-k*t),  k = CL/V
#   Renal excretion rate: dAe/dt = CLr * C(t)
#   Amount excreted in [t1, t2]: Ae(t1, t2) = CLr * AUC(t1, t2)
#   AUC(t1, t2) = (D/CL) * (exp(-k*t1) - exp(-k*t2))
#
# True analytical values:
#   Ae_inf = fe * D = (CLr/CL) * D
#   AUCinf = D / CL
#   CLr_calc = Ae_inf / AUCinf = CLr  (exact by construction)
#
# References:
#   Rowland M, Tozer TN (2011). Clinical Pharmacokinetics 4th ed., Ch. 9.
#   Shargel L, Wu-Pong S, Yu ABC (2012). Applied Biopharmaceutics 7th ed.

cat("# ================================================\n")
cat("# Urinary NCA cross-validation (independent R impl)\n")
cat("# ================================================\n\n")

# ---------------------------------------------------------------------------
# Urinary NCA formulas (same as openpkflow, coded independently in R)
# ---------------------------------------------------------------------------

# Cumulative Ae: Ae_i = volume_i * conc_i, cumsum
cumulative_ae_R <- function(volumes, concs) {
  cumsum(volumes * concs)
}

# Renal clearance
renal_clearance_R <- function(ae_total, auc_inf) {
  ae_total / auc_inf
}

# Percent excreted
percent_excreted_R <- function(ae_total, dose) {
  ae_total / dose * 100.0
}

# ---------------------------------------------------------------------------
# Synthetic dataset: 1-cmt IV bolus with renal excretion
# Subject 1: CL = 2 L/h, V = 10 L, CLr = 0.8 L/h (fe = 40%), dose = 100 mg
# Collection intervals: [0-4], [4-8], [8-12], [12-24] h
# Urine flow rate = 0.1 L/h (constant)
# ---------------------------------------------------------------------------

cat("# --- Subject 1: CL=2, V=10, CLr=0.8, dose=100, fe=0.40 ---\n")

CL   <- 2.0    # L/h
V    <- 10.0   # L
CLr  <- 0.8    # L/h (fe = 0.40)
dose <- 100.0  # mg
k    <- CL / V # 0.2 h^-1
flow <- 0.1    # L/h constant urine flow

# Analytical AUC for each collection interval
# AUC(t1,t2) = (D/CL)*(exp(-k*t1) - exp(-k*t2))
t1 <- c(0, 4,  8,  12)
t2 <- c(4, 8, 12,  24)
auc_interval <- (dose / CL) * (exp(-k * t1) - exp(-k * t2))

# True Ae per interval = CLr * AUC_interval
ae_true <- CLr * auc_interval

# Volume per interval = flow * (t2 - t1)
vol <- flow * (t2 - t1)

# Urine concentrations = Ae / volume
conc_urine <- ae_true / vol

# Collection midpoint times
t_mid <- (t1 + t2) / 2.0

cat(sprintf("# Urine collection intervals: [%s]\n",
            paste(sprintf("[%.0f-%.0f]", t1, t2), collapse=", ")))
cat(sprintf("# Volume (L):    %s\n", paste(sprintf("%.4f", vol), collapse=", ")))
cat(sprintf("# Conc (mg/L):   %s\n", paste(sprintf("%.6f", conc_urine), collapse=", ")))
cat(sprintf("# Ae per interval (mg): %s\n", paste(sprintf("%.6f", ae_true), collapse=", ")))

# Compute via R formula
ae_cum <- cumulative_ae_R(vol, conc_urine)
cat(sprintf("# Cumulative Ae (mg): %s\n", paste(sprintf("%.6f", ae_cum), collapse=", ")))

ae_total  <- ae_cum[length(ae_cum)]
auc_inf   <- dose / CL  # = 50 h*mg/L (exact)
clr_calc  <- renal_clearance_R(ae_total, auc_inf)
pct_ae    <- percent_excreted_R(ae_total, dose)

cat(sprintf("# AUCinf (h*mg/L): %.6f\n", auc_inf))
cat(sprintf("# Ae_total (mg):   %.6f\n", ae_total))
cat(sprintf("# CLr (L/h):       %.6f (true: %.4f)\n", clr_calc, CLr))
cat(sprintf("# %%Ae:             %.6f (true: %.4f%%)\n\n", pct_ae, CLr/CL*100))

# ---------------------------------------------------------------------------
# Subject 2: CL = 5 L/h, V = 20 L, CLr = 1.5 L/h (fe = 30%), dose = 200 mg
# ---------------------------------------------------------------------------

cat("# --- Subject 2: CL=5, V=20, CLr=1.5, dose=200, fe=0.30 ---\n")

CL2  <- 5.0
V2   <- 20.0
CLr2 <- 1.5
dose2 <- 200.0
k2   <- CL2 / V2

auc_interval2 <- (dose2 / CL2) * (exp(-k2 * t1) - exp(-k2 * t2))
ae_true2  <- CLr2 * auc_interval2
vol2      <- flow * (t2 - t1)
conc_urine2 <- ae_true2 / vol2

ae_cum2   <- cumulative_ae_R(vol2, conc_urine2)
ae_total2 <- ae_cum2[length(ae_cum2)]
auc_inf2  <- dose2 / CL2
clr_calc2 <- renal_clearance_R(ae_total2, auc_inf2)
pct_ae2   <- percent_excreted_R(ae_total2, dose2)

cat(sprintf("# Volume (L):    %s\n", paste(sprintf("%.4f", vol2), collapse=", ")))
cat(sprintf("# Conc (mg/L):   %s\n", paste(sprintf("%.6f", conc_urine2), collapse=", ")))
cat(sprintf("# Cumulative Ae (mg): %s\n", paste(sprintf("%.6f", ae_cum2), collapse=", ")))
cat(sprintf("# AUCinf (h*mg/L): %.6f\n", auc_inf2))
cat(sprintf("# Ae_total (mg):   %.6f\n", ae_total2))
cat(sprintf("# CLr (L/h):       %.6f (true: %.4f)\n", clr_calc2, CLr2))
cat(sprintf("# %%Ae:             %.6f (true: %.4f%%)\n\n", pct_ae2, CLr2/CL2*100))

# ---------------------------------------------------------------------------
# Subject 3: CL = 3 L/h, V = 15 L, CLr = 1.8 L/h (fe = 60%), dose = 150 mg
# ---------------------------------------------------------------------------

cat("# --- Subject 3: CL=3, V=15, CLr=1.8, dose=150, fe=0.60 ---\n")

CL3  <- 3.0
V3   <- 15.0
CLr3 <- 1.8
dose3 <- 150.0
k3   <- CL3 / V3

auc_interval3 <- (dose3 / CL3) * (exp(-k3 * t1) - exp(-k3 * t2))
ae_true3  <- CLr3 * auc_interval3
vol3      <- flow * (t2 - t1)
conc_urine3 <- ae_true3 / vol3

ae_cum3   <- cumulative_ae_R(vol3, conc_urine3)
ae_total3 <- ae_cum3[length(ae_cum3)]
auc_inf3  <- dose3 / CL3
clr_calc3 <- renal_clearance_R(ae_total3, auc_inf3)
pct_ae3   <- percent_excreted_R(ae_total3, dose3)

cat(sprintf("# Volume (L):    %s\n", paste(sprintf("%.4f", vol3), collapse=", ")))
cat(sprintf("# Conc (mg/L):   %s\n", paste(sprintf("%.6f", conc_urine3), collapse=", ")))
cat(sprintf("# Cumulative Ae (mg): %s\n", paste(sprintf("%.6f", ae_cum3), collapse=", ")))
cat(sprintf("# AUCinf (h*mg/L): %.6f\n", auc_inf3))
cat(sprintf("# Ae_total (mg):   %.6f\n", ae_total3))
cat(sprintf("# CLr (L/h):       %.6f (true: %.4f)\n", clr_calc3, CLr3))
cat(sprintf("# %%Ae:             %.6f (true: %.4f%%)\n\n", pct_ae3, CLr3/CL3*100))

# ---------------------------------------------------------------------------
# Print Python dicts for embedding in test
# ---------------------------------------------------------------------------

cat("# ============================================================\n")
cat("# Copy into tests/validation/test_nca_urine_reference.py\n")
cat("# ============================================================\n\n")

cat("_URINE_REFERENCE = {\n")

# Subject 1
cat('    "1": {\n')
cat(sprintf('        "volumes": [%s],\n', paste(sprintf("%.4f", vol), collapse=", ")))
cat(sprintf('        "concs": [%s],\n', paste(sprintf("%.6f", conc_urine), collapse=", ")))
cat(sprintf('        "auc_inf": %.6f,\n', auc_inf))
cat(sprintf('        "dose": %.1f,\n', dose))
cat(sprintf('        "ae_cumulative": [%s],\n', paste(sprintf("%.6f", ae_cum), collapse=", ")))
cat(sprintf('        "ae_total": %.6f,\n', ae_total))
cat(sprintf('        "CLr": %.6f,\n', clr_calc))
cat(sprintf('        "pct_ae": %.6f,\n', pct_ae))
cat(sprintf('        "true_CLr": %.4f,\n', CLr))
cat(sprintf('        "true_fe_pct": %.4f,\n', CLr/CL*100))
cat("    },\n")

# Subject 2
cat('    "2": {\n')
cat(sprintf('        "volumes": [%s],\n', paste(sprintf("%.4f", vol2), collapse=", ")))
cat(sprintf('        "concs": [%s],\n', paste(sprintf("%.6f", conc_urine2), collapse=", ")))
cat(sprintf('        "auc_inf": %.6f,\n', auc_inf2))
cat(sprintf('        "dose": %.1f,\n', dose2))
cat(sprintf('        "ae_cumulative": [%s],\n', paste(sprintf("%.6f", ae_cum2), collapse=", ")))
cat(sprintf('        "ae_total": %.6f,\n', ae_total2))
cat(sprintf('        "CLr": %.6f,\n', clr_calc2))
cat(sprintf('        "pct_ae": %.6f,\n', pct_ae2))
cat(sprintf('        "true_CLr": %.4f,\n', CLr2))
cat(sprintf('        "true_fe_pct": %.4f,\n', CLr2/CL2*100))
cat("    },\n")

# Subject 3
cat('    "3": {\n')
cat(sprintf('        "volumes": [%s],\n', paste(sprintf("%.4f", vol3), collapse=", ")))
cat(sprintf('        "concs": [%s],\n', paste(sprintf("%.6f", conc_urine3), collapse=", ")))
cat(sprintf('        "auc_inf": %.6f,\n', auc_inf3))
cat(sprintf('        "dose": %.1f,\n', dose3))
cat(sprintf('        "ae_cumulative": [%s],\n', paste(sprintf("%.6f", ae_cum3), collapse=", ")))
cat(sprintf('        "ae_total": %.6f,\n', ae_total3))
cat(sprintf('        "CLr": %.6f,\n', clr_calc3))
cat(sprintf('        "pct_ae": %.6f,\n', pct_ae3))
cat(sprintf('        "true_CLr": %.4f,\n', CLr3))
cat(sprintf('        "true_fe_pct": %.4f,\n', CLr3/CL3*100))
cat("    },\n")

cat("}\n\n")
cat("# Done.\n")
