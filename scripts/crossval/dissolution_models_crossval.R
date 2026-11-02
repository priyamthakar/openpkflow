#!/usr/bin/env Rscript
#
# dissolution_models_crossval.R
#
# Cross-validate openpkflow dissolution model fitting against base R optimizers
# on noise-free synthetic profiles.  No extra packages required.
#
# Strategy:
#   - Linear models (zero-order, Higuchi): lm() — exact OLS solution.
#   - Nonlinear models (first-order, KP, Weibull): optim() with Nelder-Mead
#     and tight tolerance.  For noise-free data generated from the true model,
#     the SSE global minimum is at the true parameters (SSE = 0).
#   - openpkflow scipy.optimize.curve_fit should recover the same parameters
#     to within < 1e-4 relative error.
#
# Models validated:
#   Zero-order:       Q(t) = k0 * t
#   First-order:      Q(t) = 100 * (1 - exp(-k1 * t))
#   Higuchi:          Q(t) = kH * sqrt(t)
#   Korsmeyer-Peppas: Q(t) = k * t^n
#   Weibull:          Q(t) = 100 * (1 - exp(-(t/beta)^alpha))
#
# References:
#   Costa P, Lobo JMS (2001). Eur J Pharm Sci, 13(2):123-133.
#     DOI: 10.1016/S0928-0987(01)00095-1
#   FDA Guidance: Dissolution Testing of Immediate Release Solid Oral Dosage
#     Forms (1997), CDER.

cat("# ============================================================\n")
cat("# Dissolution model fitting cross-validation (base R lm/optim)\n")
cat("# ============================================================\n\n")

t <- c(5, 10, 15, 20, 30, 45, 60, 90, 120)

# ---------------------------------------------------------------------------
# SSE helper for optim
# ---------------------------------------------------------------------------

sse <- function(pred_fn, par_names) {
  function(par) {
    names(par) <- par_names
    sum((pred_fn(par) - Q_obs)^2)
  }
}

# ---------------------------------------------------------------------------
# Zero-order: Q(t) = k0 * t  — linear in k0, use lm
# ---------------------------------------------------------------------------

cat("# --- Zero-order model: Q = k0 * t ---\n")
true_k0 <- 0.80
Q_obs   <- true_k0 * t
Q_zo    <- Q_obs
k0_fit  <- coef(lm(Q_obs ~ 0 + t))[["t"]]
cat(sprintf("# True k0 = %.6f, lm  k0 = %.10f\n", true_k0, k0_fit))
stopifnot(abs(k0_fit - true_k0) / true_k0 < 1e-6)

# ---------------------------------------------------------------------------
# First-order: Q(t) = 100*(1-exp(-k1*t)) — nonlinear, use optim
# ---------------------------------------------------------------------------

cat("# --- First-order model: Q = 100*(1-exp(-k1*t)) ---\n")
true_k1 <- 0.05
Q_fo    <- 100 * (1 - exp(-true_k1 * t))
Q_obs   <- Q_fo
fo_res  <- optim(
  par     = c(k1 = 0.08),
  fn      = function(p) sum((100 * (1 - exp(-p[1] * t)) - Q_obs)^2),
  method  = "Brent",
  lower   = 1e-5,
  upper   = 2.0,
  control = list(reltol = 1e-15)
)
k1_fit <- fo_res$par[1]
cat(sprintf("# True k1 = %.6f, optim k1 = %.10f  (SSE=%.2e)\n",
            true_k1, k1_fit, fo_res$value))
stopifnot(abs(k1_fit - true_k1) / true_k1 < 1e-5)

# ---------------------------------------------------------------------------
# Higuchi: Q(t) = kH * sqrt(t) — linear in kH, use lm
# ---------------------------------------------------------------------------

cat("# --- Higuchi model: Q = kH * sqrt(t) ---\n")
true_kH <- 8.5
Q_hi    <- true_kH * sqrt(t)
Q_obs   <- Q_hi
kH_fit  <- coef(lm(Q_obs ~ 0 + I(sqrt(t))))[["I(sqrt(t))"]]
cat(sprintf("# True kH = %.6f, lm  kH = %.10f\n", true_kH, kH_fit))
stopifnot(abs(kH_fit - true_kH) / true_kH < 1e-6)

# ---------------------------------------------------------------------------
# Korsmeyer-Peppas: Q(t) = k * t^n — linearized via log-log
# log Q = log k + n * log t  -> lm in log space
# (openpkflow also fits in Q space but recovers same params on noise-free data)
# ---------------------------------------------------------------------------

cat("# --- Korsmeyer-Peppas model: Q = k * t^n ---\n")
true_k_kp <- 3.0
true_n_kp <- 0.65
Q_kp      <- true_k_kp * t^true_n_kp
Q_obs     <- Q_kp
# Log-linearized fit: log(Q) = log(k) + n*log(t)
kp_lm    <- lm(log(Q_obs) ~ log(t))
k_kp_fit <- exp(coef(kp_lm)[["(Intercept)"]])
n_kp_fit <- coef(kp_lm)[["log(t)"]]
cat(sprintf("# True k = %.6f, lm k (log-lin) = %.10f\n", true_k_kp, k_kp_fit))
cat(sprintf("# True n = %.6f, lm n (log-lin) = %.10f\n", true_n_kp, n_kp_fit))
stopifnot(abs(k_kp_fit - true_k_kp) / true_k_kp < 1e-6)
stopifnot(abs(n_kp_fit - true_n_kp) / true_n_kp < 1e-6)

# ---------------------------------------------------------------------------
# Weibull: Q(t) = 100*(1-exp(-(t/beta)^alpha)) — 2-param optim
# ---------------------------------------------------------------------------

cat("# --- Weibull model: Q = 100*(1-exp(-(t/beta)^alpha)) ---\n")
true_alpha <- 1.5
true_beta  <- 30.0
Q_wb       <- 100 * (1 - exp(-(t / true_beta)^true_alpha))
Q_obs      <- Q_wb
wb_res  <- optim(
  par     = c(alpha = 1.2, beta = 25.0),
  fn      = function(p) {
    sum((100 * (1 - exp(-(t / p[2])^p[1])) - Q_obs)^2)
  },
  method  = "Nelder-Mead",
  control = list(reltol = 1e-14, maxit = 50000)
)
alpha_fit <- wb_res$par[1]
beta_fit  <- wb_res$par[2]
cat(sprintf("# True alpha = %.6f, optim alpha = %.10f  (SSE=%.2e)\n",
            true_alpha, alpha_fit, wb_res$value))
cat(sprintf("# True beta  = %.6f, optim beta  = %.10f\n", true_beta, beta_fit))
stopifnot(abs(alpha_fit - true_alpha) / true_alpha < 1e-4)
stopifnot(abs(beta_fit - true_beta) / true_beta < 1e-4)

cat("\n# All sanity checks passed.\n\n")

# ---------------------------------------------------------------------------
# Print Python dicts
# ---------------------------------------------------------------------------

cat("# ============================================================\n")
cat("# Copy into tests/validation/test_dissolution_models_reference.py\n")
cat("# ============================================================\n\n")

cat(sprintf("_TIMEPOINTS = %s\n\n", paste0("[", paste(t, collapse=", "), "]")))

cat("_MODEL_REFERENCE = {\n")

cat('    "zero_order": {\n')
cat(sprintf('        "true_k0": %.4f,\n', true_k0))
cat(sprintf('        "ref_k0": %.10f,\n', k0_fit))
cat(sprintf('        "Q": [%s],\n', paste(sprintf("%.10f", Q_zo), collapse=", ")))
cat("    },\n")

cat('    "first_order": {\n')
cat(sprintf('        "true_k1": %.4f,\n', true_k1))
cat(sprintf('        "ref_k1": %.10f,\n', k1_fit))
cat(sprintf('        "Q": [%s],\n', paste(sprintf("%.10f", Q_fo), collapse=", ")))
cat("    },\n")

cat('    "higuchi": {\n')
cat(sprintf('        "true_kH": %.4f,\n', true_kH))
cat(sprintf('        "ref_kH": %.10f,\n', kH_fit))
cat(sprintf('        "Q": [%s],\n', paste(sprintf("%.10f", Q_hi), collapse=", ")))
cat("    },\n")

cat('    "korsmeyer_peppas": {\n')
cat(sprintf('        "true_k": %.4f,\n', true_k_kp))
cat(sprintf('        "true_n": %.4f,\n', true_n_kp))
cat(sprintf('        "ref_k": %.10f,\n', k_kp_fit))
cat(sprintf('        "ref_n": %.10f,\n', n_kp_fit))
cat(sprintf('        "Q": [%s],\n', paste(sprintf("%.10f", Q_kp), collapse=", ")))
cat("    },\n")

cat('    "weibull": {\n')
cat(sprintf('        "true_alpha": %.4f,\n', true_alpha))
cat(sprintf('        "true_beta": %.4f,\n', true_beta))
cat(sprintf('        "ref_alpha": %.10f,\n', alpha_fit))
cat(sprintf('        "ref_beta": %.10f,\n', beta_fit))
cat(sprintf('        "Q": [%s],\n', paste(sprintf("%.10f", Q_wb), collapse=", ")))
cat("    },\n")

cat("}\n\n")
cat("# Done.\n")
