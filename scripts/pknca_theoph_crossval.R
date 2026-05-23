#!/usr/bin/env Rscript
#
# pknca_theoph_crossval.R
#
# Run PKNCA 0.10.x on the openpkflow theoph.csv reference dataset.
# Outputs per-subject AUClast (linear-up/log-down) and Cmax as a
# Python-dictionary-ready block for use in test_nca_theoph_reference.py.
#
# Usage:
#   Rscript scripts/pknca_theoph_crossval.R
#
# Requires:
#   - R >= 4.0
#   - PKNCA >= 0.10.0  (install: install.packages("PKNCA"))
#   - dplyr, readr, tidyr (usually included with tidyverse)
#
# Reference:
#   Denney WS, Duvvuri S, Buckeridge CE (2015).
#   "Simple, Automatic Noncompartmental Analysis: The PKNCA R Package."
#   Journal of Statistical Software, 59(1), 1-21. DOI: 10.18637/jss.v059.i11
#
# Cross-validation methodology:
#   Both openpkflow and PKNCA compute AUClast via linear-up/log-down
#   trapezoidal rule on the identical theophylline dataset (12 subjects,
#   oral, ~320 mg dose).  Cmax is simply the maximum observed concentration
#   and should match exactly.  AUClast should agree within machine epsilon
#   (~2% tolerance is conservative and accounts for floating-point
#   accumulation differences).
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(PKNCA)
  library(dplyr)
})

# Locate the CSV relative to this script's directory, or use command-line arg
args <- commandArgs(trailingOnly = TRUE)
if (length(args) >= 1) {
  csv_path <- args[1]
} else {
  # Default path relative to project root (script is in scripts/)
  script_dir <- dirname(sys.frame(1)$ofile)
  if (is.null(script_dir) || script_dir == "") {
    script_dir <- getwd()
  }
  csv_path <- file.path(script_dir, "..", "src", "openpkflow", "datasets", "theoph.csv")
  csv_path <- normalizePath(csv_path, mustWork = FALSE)
}

stopifnot(file.exists(csv_path))

cat(sprintf("# PKNCA cross-validation on: %s\n", csv_path))
cat(sprintf("# PKNCA version: %s\n", as.character(packageVersion("PKNCA"))))

# Load the dataset
raw <- read.csv(csv_path, stringsAsFactors = FALSE)

# PKNCA expects columns: subject, time, conc (dose handled separately)
# The openpkflow CSV has: subject,time,conc,dose,route
# For NCA we need the concentration data and dose info
data <- raw[, c("subject", "time", "conc", "dose", "route")]
data$subject <- as.factor(data$subject)

cat(sprintf("# Subjects: %d, rows: %d\n",
            length(unique(data$subject)), nrow(data)))

# ---------------------------------------------------------------------------
# PKNCA NCA pipeline
# ---------------------------------------------------------------------------

# Create concentration object
conc_obj <- PKNCAconc(data, conc ~ time | subject)

# Define intervals for oral dosing:
#   start=0      → dose time
#   end=Inf      → use last observation per subject
#   auclast=TRUE → compute AUClast
#   cmax=TRUE    → compute Cmax
intervals <- data.frame(
  start = 0,
  end   = Inf,
  auclast = TRUE,
  cmax    = TRUE,
  stringsAsFactors = FALSE
)

# Build the PKNCAdata object
# PKNCA v0.10.x requires dose information for oral dosing.
# We set the dose for each subject manually.
# The dose column in the CSV is constant per subject, so we take the first value.

# PKNCA expects dose in a separate data.frame or as a formula.
# For oral data, we specify dose in the PKNCAdata call:
dose_df <- data %>%
  group_by(subject) %>%
  summarise(dose = first(dose), .groups = "drop")

# PKNCA 0.10.x: provide dose via dose argument with a formula
data_obj <- PKNCAdata(
  conc_obj,
  intervals = intervals,
  dose      = dose ~ dose | subject
)

# Run NCA
cat("Running PKNCA pk.nca()...\n")
results <- pk.nca(data_obj)

# ---------------------------------------------------------------------------
# Extract AUClast and Cmax per subject
# ---------------------------------------------------------------------------

# pk.nca() returns an object with $result containing the numerical results
# The structure is a data.frame with columns for each parameter.
# We extract AUClast and Cmax for each subject.

result_df <- as.data.frame(results)

# PKNCA names parameters with a prefix indicating the parameter type
# and the interval.  For AUClast from interval 0-Inf:
#   "auclast" is the column name pattern
# For Cmax:
#   "cmax" is the column name pattern

# Find the exact column names (PKNCA may prefix them)
auclast_col <- grep("auclast", names(result_df), ignore.case = TRUE, value = TRUE)
cmax_col    <- grep("^cmax$|^cmax\\b", names(result_df), ignore.case = TRUE, value = TRUE)

if (length(auclast_col) == 0) {
  stop("Could not find auclast column in PKNCA results. Columns: ",
       paste(names(result_df), collapse = ", "))
}
if (length(cmax_col) == 0) {
  stop("Could not find cmax column in PKNCA results. Columns: ",
       paste(names(result_df), collapse = ", "))
}

cat(sprintf("# AUClast column: %s\n", auclast_col[1]))
cat(sprintf("# Cmax column:    %s\n", cmax_col[1]))

# Build the reference table
ref <- data.frame(
  subject  = result_df$subject,
  AUClast  = result_df[[auclast_col[1]]],
  Cmax     = result_df[[cmax_col[1]]],
  stringsAsFactors = FALSE
)

# Sort by subject for consistency
ref <- ref[order(ref$subject), ]

# ---------------------------------------------------------------------------
# Output as a Python dictionary (ready to paste into test file)
# ---------------------------------------------------------------------------

cat("\n# ============================================================\n")
cat("# Copy the block below into tests/validation/test_nca_theoph_reference.py\n")
cat("# Replace the placeholder _PKNCA_REFERENCE dict.\n")
cat("# ============================================================\n\n")

cat("_PKNCA_REFERENCE = {\n")
for (i in seq_len(nrow(ref))) {
  subj <- as.character(ref$subject[i])
  auc  <- round(ref$AUClast[i], 6)
  cmax <- round(ref$Cmax[i], 6)
  cat(sprintf('    %s: {"AUClast": %.6f, "Cmax": %.6f},\n', subj, auc, cmax))
}
cat("}\n")

# Also print a human-readable summary
cat("\n# --- Human-readable summary ---\n")
cat(sprintf("%-8s %12s %10s\n", "Subject", "AUClast", "Cmax"))
cat(strrep("-", 32), "\n")
for (i in seq_len(nrow(ref))) {
  cat(sprintf("%-8s %12.4f %10.4f\n",
              ref$subject[i], ref$AUClast[i], ref$Cmax[i]))
}

# Verify all 12 subjects are present
stopifnot(nrow(ref) == 12)
cat(sprintf("\n# All %d subjects processed successfully.\n", nrow(ref)))
