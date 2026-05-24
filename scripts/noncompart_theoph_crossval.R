#!/usr/bin/env Rscript
#
# noncompart_theoph_crossval.R
#
# Second independent NCA cross-validation: NonCompart 0.8.x on the
# 12-subject theophylline dataset vs openpkflow.
#
# Usage:
#   Rscript scripts/noncompart_theoph_crossval.R
#
# Requires: R >= 4.0, NonCompart >= 0.8.0
#
# References:
#   Kim S, Kim J (2024). NonCompart: Noncompartmental Analysis for
#   Pharmacokinetic Data. R package. CRAN.
#
# Unit note:
#   When concUnit="mg/L" is passed to sNCA(), NonCompart uses SI-consistent
#   units: dose (mg) / AUC (mg*h/L) = L/h, so CLFO and VZFO are already in
#   L/h and L respectively.  No unit conversion is needed.
#   (Without concUnit, NonCompart defaults to mL/h and mL -- 1000x larger.)

suppressPackageStartupMessages(library(NonCompart))

csv_path <- "D:/openpkflow/src/openpkflow/datasets/theoph.csv"
stopifnot(file.exists(csv_path))

cat(sprintf("# Dataset: %s\n", csv_path))
cat(sprintf("# NonCompart version: %s\n", as.character(packageVersion("NonCompart"))))

raw      <- read.csv(csv_path, stringsAsFactors = FALSE)
subjects <- sort(unique(raw$subject))
cat(sprintf("# Subjects: %d\n", length(subjects)))

# ---------------------------------------------------------------------------
# Run sNCA per subject (per-subject doses require a loop)
# ---------------------------------------------------------------------------

records <- list()
for (s in subjects) {
  sub   <- raw[raw$subject == s, ]
  dose  <- sub$dose[1]
  r     <- sNCA(
    sub$time, sub$conc,
    dose     = dose,
    adm      = "Extravascular",
    dur      = 0,
    down     = "Log",        # linear-up log-down
    timeUnit = "h",
    concUnit = "mg/L"
  )
  records[[as.character(s)]] <- r
}

cat(sprintf("# Parameters: %s\n", paste(names(records[[1]]), collapse = ", ")))

# ---------------------------------------------------------------------------
# Print Python dict
# ---------------------------------------------------------------------------

cat("\n# ============================================================\n")
cat("# Copy into tests/validation/test_nca_noncompart_reference.py\n")
cat("# as _NONCOMPART_REFERENCE\n")
cat("# CL (CLFO) and V (VZFO) already in L/h and L when concUnit='mg/L'.\n")
cat("# ============================================================\n\n")

cat("_NONCOMPART_REFERENCE = {\n")
for (s in as.character(subjects)) {
  r <- records[[s]]
  cat(sprintf(
    '    "%s": {\n        "AUClast": %.6f, "Cmax": %.6f, "Tmax": %.4f,\n',
    s, r["AUCLST"], r["CMAX"], r["TMAX"]
  ))
  cat(sprintf(
    '        "AUCinf_obs": %.6f, "AUC_pct_extrap": %.4f,\n',
    r["AUCIFO"], r["AUCPEO"]
  ))
  cat(sprintf(
    '        "half_life": %.6f, "lambda_z": %.8f,\n',
    r["LAMZHL"], r["LAMZ"]
  ))
  cat(sprintf(
    '        "adj_r2": %.6f, "n_points": %d,\n',
    r["R2ADJ"], as.integer(r["LAMZNPT"])
  ))
  cat(sprintf(
    '        "CL_F": %.6f, "Vz_F": %.6f,\n    },\n',
    r["CLFO"], r["VZFO"]
  ))
}
cat("}\n")

# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------

cat("\n# --- Human-readable summary ---\n")
cat(sprintf("%-8s %10s %8s %8s %12s %10s %10s %10s %10s %6s %10s %10s\n",
            "Subject", "AUClast", "Cmax", "Tmax", "AUCinf_obs",
            "AUCpext%", "half_life", "lambda_z", "adj_R2", "n_pts", "CL_F", "Vz_F"))
cat(strrep("-", 115), "\n")
for (s in as.character(subjects)) {
  r <- records[[s]]
  cat(sprintf(
    "%-8s %10.4f %8.4f %8.4f %12.4f %10.4f %10.4f %10.6f %10.6f %6d %10.4f %10.4f\n",
    s, r["AUCLST"], r["CMAX"], r["TMAX"], r["AUCIFO"],
    r["AUCPEO"], r["LAMZHL"], r["LAMZ"],
    r["R2ADJ"], as.integer(r["LAMZNPT"]),
    r["CLFO"], r["VZFO"]
  ))
}

stopifnot(length(records) == 12)
cat(sprintf("\n# All %d subjects processed successfully.\n", length(records)))
