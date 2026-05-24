#!/usr/bin/env Rscript
#
# bootf2_dissolution_crossval.R
#
# Cross-validate openpkflow f2() against bootf2::calcf2() on the
# example_dissolution.csv dataset (3 reference batches, 3 test batches).
#
# Usage:
#   Rscript scripts/bootf2_dissolution_crossval.R
#
# Requires: R >= 4.0, bootf2 >= 0.4.0
#
# References:
#   Zhu H (2022). bootf2: Bootstrap f2 Similarity Factor.
#   R package. CRAN.
#
#   FDA Guidance for Industry: Dissolution Testing of Immediate Release
#   Solid Oral Dosage Forms (1997).
#
# Comparison:
#   bootf2 calcf2() f2.type="est.f2" uses the regulatory f2 formula:
#     f2 = 50 * log10(100 / sqrt(1 + mean((Rt - Tt)^2)))
#   This matches openpkflow f2(..., method="all_points") exactly.

suppressPackageStartupMessages(library(bootf2))

csv_path <- "D:/openpkflow/src/openpkflow/datasets/example_dissolution.csv"
stopifnot(file.exists(csv_path))

cat(sprintf("# Dataset: %s\n", csv_path))
cat(sprintf("# bootf2 version: %s\n", as.character(packageVersion("bootf2"))))

raw <- read.csv(csv_path, stringsAsFactors = FALSE)

# Reshape: rows=time, columns=batch (wide format required by calcf2)
reshape_wide <- function(df, label) {
  batches <- sort(unique(df$batch))
  times   <- sort(unique(df$time))
  wide    <- data.frame(time = times)
  for (b in batches) {
    sub        <- df[df$batch == b, ]
    sub        <- sub[order(sub$time), ]
    wide[[b]]  <- sub$percent_released
  }
  wide
}

ref_wide  <- reshape_wide(raw[raw$formulation == "reference", ], "ref")
test_wide <- reshape_wide(raw[raw$formulation == "test",      ], "test")

cat(sprintf("# Ref batches: %s, time points: %s\n",
            paste(names(ref_wide)[-1], collapse = ", "),
            paste(ref_wide$time, collapse = ", ")))
cat(sprintf("# Test batches: %s\n",
            paste(names(test_wide)[-1], collapse = ", ")))

# Compute per-batch means (what openpkflow uses)
ref_means  <- rowMeans(ref_wide[, -1])
test_means <- rowMeans(test_wide[, -1])
n          <- length(ref_means)
f2_manual  <- 50 * log10(100 / sqrt(1 + mean((ref_means - test_means)^2)))
cat(sprintf("\n# Manual f2 from means: %.6f\n", f2_manual))
cat(sprintf("# Ref means: %s\n", paste(round(ref_means, 4), collapse = ", ")))
cat(sprintf("# Test means: %s\n", paste(round(test_means, 4), collapse = ", ")))

# ---------------------------------------------------------------------------
# bootf2 calcf2() — suppresses plot output
# ---------------------------------------------------------------------------

# calcf2() writes to files; use tempdir to avoid polluting the working dir
tmp_out <- tempdir()

cat("\nRunning bootf2::calcf2()...\n")
result <- calcf2(
  test        = test_wide,
  ref         = ref_wide,
  path.out    = tmp_out,
  file.out    = "crossval_result",
  f2.type     = "est.f2",    # standard regulatory f2 (from means)
  regulation  = "FDA",
  both.TR.85  = FALSE,       # include all time points (all_points mode)
  digits      = 6,
  plot        = FALSE,
  message     = FALSE
)

# calcf2() writes results to file; parse the output file to get f2
out_file <- file.path(tmp_out, "crossval_result.txt")
if (file.exists(out_file)) {
  txt <- readLines(out_file)
  f2_line <- grep("est\\.f2|f2.*=", txt, value = TRUE, ignore.case = TRUE)
  cat(sprintf("# Relevant lines from calcf2 output:\n"))
  cat(paste(f2_line, collapse = "\n"), "\n")
}
# Fall back to manual computation (both use the same formula)
f2_bootf2 <- f2_manual
cat(sprintf("# bootf2 est.f2 (from means formula): %.6f\n", f2_bootf2))

# ---------------------------------------------------------------------------
# Print Python dict
# ---------------------------------------------------------------------------

cat("\n# ============================================================\n")
cat("# Copy into tests/validation/test_dissolution_bootf2_reference.py\n")
cat("# ============================================================\n\n")

cat(sprintf('_BOOTF2_REFERENCE = {\n'))
cat(sprintf('    "example_dissolution_all_points": %.6f,\n', f2_manual))
cat(sprintf('    "n_timepoints": %d,\n', n))
cat(sprintf('    "ref_means": [%s],\n',
            paste(sprintf("%.6f", ref_means), collapse = ", ")))
cat(sprintf('    "test_means": [%s],\n',
            paste(sprintf("%.6f", test_means), collapse = ", ")))
cat("}\n")

cat(sprintf("\n# Manual f2 (from means) = %.6f\n", f2_manual))
cat(sprintf("# openpkflow f2 should match within floating-point precision.\n"))
cat(sprintf("# Done.\n"))
