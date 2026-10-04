#!/usr/bin/env Rscript
#
# pknca_lambda_z_tolerance_crossval.R
#
# Reference values for the lambda_z auto-selection adjusted R-squared
# tolerance (PKNCA adj.r.squared.factor, default 1e-4). Two constructed oral
# profiles are run through PKNCA::pk.calc.half.life():
#   near: a 5-point window is within 1e-4 of the best (4-point) adjusted R2,
#         so PKNCA selects 5 points; with the factor ~0 it selects 4.
#   far:  every longer window is > 1e-4 worse, so PKNCA keeps 3 points.
# Output feeds tests/validation/test_nca_lambda_z_pknca_tolerance.py.
#
# Usage:
#   Rscript scripts/pknca_lambda_z_tolerance_crossval.R
#
# Requires: R >= 4.1, PKNCA >= 0.12.1
#
# Reference:
#   PKNCA R package (Denney WS, Buckeridge C, Rodriguez GJ),
#   https://github.com/humanpred/pknca, pk.calc.half.life() documentation
#   (log-linear selection: best adjusted R2 within adj.r.squared.factor,
#   then the most points).
# ---------------------------------------------------------------------------

suppressPackageStartupMessages(library(PKNCA))
cat(sprintf("# PKNCA %s, %s\n", packageVersion("PKNCA"), R.version.string))

times <- c(0, 0.5, 1, 2, 4, 6, 8, 12, 16, 24)
profiles <- list(
  near = c(0.0, 4.654, 6.191, 6.865, 5.359, 4.163, 3.017, 1.634, 0.879, 0.27),
  far  = c(0.0, 4.706, 6.461, 6.559, 5.665, 4.138, 2.948, 1.692, 0.921, 0.276)
)
for (name in names(profiles)) {
  for (factor in c(1e-4, 1e-12)) {
    hl <- suppressWarnings(
      pk.calc.half.life(conc = profiles[[name]], time = times, tlast = 24,
                        adj.r.squared.factor = factor))
    cat(sprintf("%s factor=%g lambda_z=%.15g adj_r2=%.15g n_points=%d half_life=%.15g\n",
                name, factor, hl$lambda.z, hl$adj.r.squared,
                as.integer(hl$lambda.z.n.points), hl$half.life))
  }
}
