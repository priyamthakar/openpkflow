#!/usr/bin/env Rscript
#
# powertost_crossval.R
#
# Cross-validate openpkflow be_tost_power() and be_sample_size() against
# PowerTOST 1.5-7.
#
# Usage:
#   Rscript scripts/powertost_crossval.R
#
# Requires: R >= 4.0, PowerTOST >= 1.5
#
# References:
#   Labes D, Schutz H, Lang B (2024). PowerTOST: Power and Sample Size
#   for (Bio)Equivalence Studies. R package, CRAN.
#
#   Diletti E, Hauschke D, Steinijans VW (1991). Sample size determination
#   for bioequivalence assessment by means of confidence intervals.
#   Int J Clin Pharmacol Ther Toxicol, 29(1):1-8.
#
#   Phillips KF (1990). Power of the two one-sided tests procedure in
#   bioequivalence. J Pharmacokinet Biopharm, 18(2):137-144.

suppressPackageStartupMessages(library(PowerTOST))

cat("# ============================================================\n")
cat("# PowerTOST cross-validation for openpkflow BE power/sample\n")
cat(sprintf("# PowerTOST version: %s\n", as.character(packageVersion("PowerTOST"))))
cat("# ============================================================\n\n")

# ---------------------------------------------------------------------------
# Power scenarios (power.TOST)
# ---------------------------------------------------------------------------

power_scenarios <- list(
  list(theta0 = 0.95, CV = 0.15, n = 24),
  list(theta0 = 1.00, CV = 0.20, n = 18),
  list(theta0 = 0.90, CV = 0.25, n = 36),
  list(theta0 = 1.05, CV = 0.10, n = 12),
  list(theta0 = 0.80, CV = 0.30, n = 48),
  list(theta0 = 0.95, CV = 0.35, n = 40)
)

cat("# Power scenarios\n")
cat("_POWERTOST_POWER_REFERENCE = {\n")
for (i in seq_along(power_scenarios)) {
  s <- power_scenarios[[i]]
  p <- power.TOST(
    theta0 = s$theta0, CV = s$CV, n = s$n,
    design = "2x2", method = "exact"
  )
  cat(sprintf('    "%d": {\n', i))
  cat(sprintf('        "GMR": %.2f,\n', s$theta0))
  cat(sprintf('        "CV": %.2f,\n', s$CV))
  cat(sprintf('        "n": %d,\n', s$n))
  cat(sprintf('        "power": %.10f,\n', p))
  cat('    },\n')
}
cat("}\n\n")

# ---------------------------------------------------------------------------
# Sample size scenarios (sampleN.TOST)
# ---------------------------------------------------------------------------

ss_scenarios <- list(
  list(targetpower = 0.80, theta0 = 0.95, CV = 0.20),
  list(targetpower = 0.90, theta0 = 0.95, CV = 0.15),
  list(targetpower = 0.80, theta0 = 0.90, CV = 0.25),
  list(targetpower = 0.80, theta0 = 1.00, CV = 0.10),
  list(targetpower = 0.90, theta0 = 0.95, CV = 0.30),
  list(targetpower = 0.80, theta0 = 0.85, CV = 0.15)
)

cat("# Sample size scenarios\n")
cat("_POWERTOST_SAMPLE_SIZE_REFERENCE = {\n")
for (i in seq_along(ss_scenarios)) {
  s <- ss_scenarios[[i]]
  result <- sampleN.TOST(
    targetpower = s$targetpower, theta0 = s$theta0, CV = s$CV,
    design = "2x2", method = "exact", print = FALSE, details = FALSE
  )
  n_val <- as.integer(result[["Sample size"]])
  ach_pwr <- result[["Achieved power"]]
  cat(sprintf('    "%d": {\n', i))
  cat(sprintf('        "target_power": %.2f,\n', s$targetpower))
  cat(sprintf('        "GMR": %.2f,\n', s$theta0))
  cat(sprintf('        "CV": %.2f,\n', s$CV))
  cat(sprintf('        "n": %d,\n', n_val))
  cat(sprintf('        "achieved_power": %.10f,\n', ach_pwr))
  cat('    },\n')
}
cat("}\n\n")

cat("# Done.\n")
cat("# Copy the dictionaries above into tests/validation/test_be_power_reference.py\n")
