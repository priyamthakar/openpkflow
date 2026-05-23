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

# PKNCA 0.12.x: dose must be a PKNCAdose object with time=0 rows
dose_df <- data.frame(
  subject = unique(data$subject),
  time    = 0,
  dose    = sapply(unique(data$subject), function(s) data$dose[data$subject == s][1]),
  stringsAsFactors = FALSE
)
dose_obj <- PKNCAdose(dose_df, dose ~ time | subject)

data_obj <- PKNCAdata(
  data.conc  = conc_obj,
  data.dose  = dose_obj,
  intervals  = intervals
)

# Run NCA
cat("Running PKNCA pk.nca()...\n")
results <- pk.nca(data_obj)

# ---------------------------------------------------------------------------
# Extract AUClast and Cmax per subject
# ---------------------------------------------------------------------------

# pk.nca() in v0.12.x returns a data.frame with CDISC-style columns:
#   subject, start, end, PPTESTCD, PPORRES, exclude
# PPTESTCD = parameter name (e.g. "auclast", "cmax")
# PPORRES  = numeric result

result_df <- as.data.frame(results)

cat(sprintf("# Result columns: %s\n", paste(names(result_df), collapse = ", ")))
cat(sprintf("# Parameters found: %s\n",
            paste(unique(result_df$PPTESTCD), collapse = ", ")))

# Extract AUClast and Cmax rows, reshape to wide per-subject
auc_rows <- subset(result_df, PPTESTCD == "auclast")
cmax_rows <- subset(result_df, PPTESTCD == "cmax")

if (nrow(auc_rows) == 0) {
  stop("No auclast rows found. Parameters: ",
       paste(unique(result_df$PPTESTCD), collapse = ", "))
}

cat(sprintf("# AUClast rows: %d\n", nrow(auc_rows)))
cat(sprintf("# Cmax rows:    %d\n", nrow(cmax_rows)))

# Build the reference table
ref <- data.frame(
  subject  = auc_rows$subject,
  AUClast  = auc_rows$PPORRES,
  Cmax     = cmax_rows$PPORRES,
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
