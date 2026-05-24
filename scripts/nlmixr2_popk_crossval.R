#!/usr/bin/env Rscript
#
# nlmixr2_popk_crossval.R
#
# Fit a 1-compartment oral pop PK model with FOCE-I in nlmixr2 5.0.0
# to the 12-subject Theophylline dataset (Pinheiro & Bates 2000, Table A.1).
#
# Outputs population typical values, IIV (omega^2 diagonal), residual sigma,
# and EBEs formatted as a Python dict for use in test_pop_foce_reference.py.
#
# Usage (from project root):
#   "C:\Program Files\R\R-4.6.0\bin\Rscript.exe" scripts/nlmixr2_popk_crossval.R
#
# Requires: nlmixr2 >= 5.0.0  (installed at D:/R-library/4.6)
#
# Reference:
#   Pinheiro JC, Bates DM (2000). Mixed-Effects Models in S and S-PLUS.
#   Springer, New York. Table A.1 (Theophylline data).
#
#   Fidler M, et al. (2019). nlmixr: Nonlinear mixed-effects models in R.
#   CPT Pharmacometrics Syst. Pharmacol. DOI: 10.1002/psp4.12445
#
# Cross-validation strategy:
#   nlmixr2 FOCE-I and openpkflow FOCE-I both minimize the same FOCE-I
#   objective (-2LL with conditional linearisation) on the same 1-cmt oral
#   model. Parameter estimates differ due to optimizer tolerance, numerical
#   Hessian differences, and inner-loop convergence criteria. A 20% relative
#   tolerance is appropriate per HANDOFF.md.
# ---------------------------------------------------------------------------

.libPaths("D:/R-library/4.6")

suppressPackageStartupMessages({
  library(nlmixr2)
})

# --- Locate dataset ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) >= 1) {
  csv_path <- args[1]
} else {
  script_dir <- tryCatch(
    dirname(sys.frame(1)$ofile),
    error = function(e) getwd()
  )
  if (is.null(script_dir) || script_dir == "") script_dir <- getwd()
  csv_path <- normalizePath(
    file.path(script_dir, "..", "src", "openpkflow", "datasets", "theoph.csv"),
    mustWork = FALSE
  )
}

stopifnot(file.exists(csv_path))
cat(sprintf("# Dataset: %s\n", csv_path))
cat(sprintf("# nlmixr2 version: %s\n", as.character(packageVersion("nlmixr2"))))

# --- Build NONMEM-style dataset ---
raw <- read.csv(csv_path, stringsAsFactors = FALSE)

# Each subject needs: dosing row (EVID=1, AMT=dose, DV=0) at TIME=0,
# followed by observation rows (EVID=0, AMT=0, DV=conc, TIME>0).
obs_rows <- raw[raw$time > 0, ]

dose_rows <- data.frame(
  ID   = unique(raw$subject),
  TIME = 0,
  AMT  = sapply(unique(raw$subject), function(s) raw$dose[raw$subject == s][1]),
  DV   = 0,
  EVID = 1,
  stringsAsFactors = FALSE
)

obs_df <- data.frame(
  ID   = obs_rows$subject,
  TIME = obs_rows$time,
  AMT  = 0,
  DV   = obs_rows$conc,
  EVID = 0,
  stringsAsFactors = FALSE
)

# Combine and sort: by ID, TIME, then DESC EVID (dose before obs at TIME=0)
dat <- rbind(dose_rows, obs_df)
dat <- dat[order(dat$ID, dat$TIME, -dat$EVID), ]
dat$ID <- as.integer(factor(dat$ID))   # nlmixr2 needs integer IDs

cat(sprintf("# Subjects: %d  Rows: %d  Obs: %d\n",
            length(unique(dat$ID)), nrow(dat), sum(dat$EVID == 0)))

# --- nlmixr2 model: 1-cmt oral, proportional + additive residual error ---
one_cmt_oral <- function() {
  ini({
    # Population log-typical values
    lCL  <- log(3.0)   # CL/F (L/h)
    lV   <- log(30.0)  # V/F  (L)
    lKa  <- log(1.5)   # ka   (1/h)

    # IIV (eta ~ N(0, omega^2), on log scale)
    eta.CL  ~ 0.1
    eta.V   ~ 0.1
    eta.Ka  ~ 0.1

    # Residual error
    prop.err <- 0.15
    add.err  <- 0.1
  })

  model({
    CL <- exp(lCL + eta.CL)
    V  <- exp(lV  + eta.V)
    ka <- exp(lKa + eta.Ka)

    linCmt() ~ prop(prop.err) + add(add.err)
  })
}

cat("# Fitting 1-cmt oral model with FOCE-I (this may take 1-3 min)...\n")

fit <- tryCatch(
  nlmixr2(one_cmt_oral, dat, est = "focei",
          control = foceiControl(maxOuterIterations = 10000,
                                 outerOpt = "lbfgsb3c",
                                 covMethod = "")),
  error = function(e) {
    cat(sprintf("# ERROR: %s\n", conditionMessage(e)))
    NULL
  }
)

if (is.null(fit)) {
  stop("nlmixr2 fit failed -- see error above")
}

# --- Extract population typical values ---
cat("\n# ============================================================\n")
cat("# nlmixr2 5.0.0  FOCE-I  1-cmt oral  Theoph (12 subjects)\n")
cat("# ============================================================\n\n")

# Fixed effects (exp-transformed to natural scale)
fe <- fit$parFixed
cat("# Fixed effects (natural scale):\n")
print(fe)

cl_pop <- exp(fit$theta["lCL"])
v_pop  <- exp(fit$theta["lV"])
ka_pop <- exp(fit$theta["lKa"])

# IIV omega^2 (variance of random effects)
omega_mat <- fit$omega
cat("\n# Omega (variance-covariance matrix of random effects):\n")
print(omega_mat)

omega_cl <- omega_mat["eta.CL", "eta.CL"]
omega_v  <- omega_mat["eta.V",  "eta.V"]
omega_ka <- omega_mat["eta.Ka", "eta.Ka"]

# Residual error sigmas
sigma_prop <- fit$theta["prop.err"]
sigma_add  <- fit$theta["add.err"]

cat(sprintf("\n# CL_F  = %.6f\n", cl_pop))
cat(sprintf("# Vz_F  = %.6f\n", v_pop))
cat(sprintf("# ka    = %.6f\n", ka_pop))
cat(sprintf("# omega_CL  = %.6f  (IIV variance)\n", omega_cl))
cat(sprintf("# omega_V   = %.6f\n", omega_v))
cat(sprintf("# omega_ka  = %.6f\n", omega_ka))
cat(sprintf("# sigma_prop = %.6f\n", sigma_prop))
cat(sprintf("# sigma_add  = %.6f\n", sigma_add))

# --- EBEs (individual empirical Bayes estimates) ---
ebe_df <- fit$eta
cat("\n# EBEs (eta per subject):\n")
print(ebe_df)

# --- Python dict output ---
cat("\n# ============================================================\n")
cat("# Copy block below into test_pop_foce_reference.py\n")
cat("# ============================================================\n\n")

cat("_NLMIXR2_REFERENCE = {\n")
cat(sprintf('    "CL_F":      %.6f,\n', cl_pop))
cat(sprintf('    "Vz_F":      %.6f,\n', v_pop))
cat(sprintf('    "ka":        %.6f,\n', ka_pop))
cat(sprintf('    "omega_CL":  %.6f,\n', omega_cl))
cat(sprintf('    "omega_Vz":  %.6f,\n', omega_v))
cat(sprintf('    "omega_ka":  %.6f,\n', omega_ka))
cat(sprintf('    "sigma_prop": %.6f,\n', sigma_prop))
cat(sprintf('    "sigma_add":  %.6f,\n', sigma_add))
cat("}\n")

cat(sprintf("\n# OFV (-2LL) = %.4f\n", fit$objective))
cat(sprintf("# AIC       = %.4f\n", fit$AIC))

cat("\n# All done.\n")
