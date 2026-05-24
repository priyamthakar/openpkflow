#!/usr/bin/env Rscript
#
# pknca_ss_crossval.R
#
# Cross-validate openpkflow steady-state NCA parameters against PKNCA 0.12.1
# on a synthetic 3-subject dataset generated from the 1-compartment oral
# steady-state model.
#
# Usage:
#   Rscript scripts/pknca_ss_crossval.R
#
# Requires:
#   - R >= 4.0
#   - PKNCA >= 0.12.0
#   - dplyr
#
# Parameters validated:
#   AUCtau, Cmax_ss, Cmin_ss, Cavg_ss, fluctuation_pct (deg.fluc), swing
#
# Reference:
#   Denney WS, Duvvuri S, Buckeridge CE (2015).
#   "Simple, Automatic Noncompartmental Analysis: The PKNCA R Package."
#   Journal of Statistical Software, 59(1), 1-21. DOI: 10.18637/jss.v059.i11

suppressPackageStartupMessages({
  library(PKNCA)
  library(dplyr)
})

csv_path <- "D:/openpkflow/src/openpkflow/datasets/ss_crossval.csv"
stopifnot(file.exists(csv_path))

TAU <- 8.0  # dosing interval in hours

cat(sprintf("# Dataset: %s\n", csv_path))
cat(sprintf("# PKNCA version: %s\n", as.character(packageVersion("PKNCA"))))
cat(sprintf("# tau = %.1f h\n", TAU))

raw  <- read.csv(csv_path, stringsAsFactors = FALSE)
data <- raw[, c("subject", "time", "conc", "dose", "route")]
data$subject <- as.factor(data$subject)

cat(sprintf("# Subjects: %s, rows: %d\n",
            paste(sort(unique(as.character(data$subject))), collapse = ", "),
            nrow(data)))

# ---------------------------------------------------------------------------
# PKNCA pipeline — steady-state interval [0, tau]
# ---------------------------------------------------------------------------

conc_obj <- PKNCAconc(data, conc ~ time | subject)

dose_df <- data.frame(
  subject = unique(data$subject),
  time    = 0,
  dose    = sapply(unique(data$subject),
                   function(s) data$dose[data$subject == s][1]),
  stringsAsFactors = FALSE
)
dose_obj <- PKNCAdose(dose_df, dose ~ time | subject)

# For steady-state analysis on a closed [0, tau] interval:
#   auclast  -> AUCtau  (last obs at tau closes the interval)
#   cmax     -> Cmax_ss
#   cmin     -> Cmin_ss
#   cav      -> Cavg_ss = AUCtau / tau
#   deg.fluc -> fluctuation_pct = (Cmax-Cmin)/Cavg * 100
#   swing    -> (Cmax-Cmin)/Cmin
intervals <- data.frame(
  start    = 0,
  end      = TAU,
  auclast  = TRUE,
  cmax     = TRUE,
  cmin     = TRUE,
  cav      = TRUE,
  deg.fluc = TRUE,
  swing    = TRUE,
  stringsAsFactors = FALSE
)

data_obj <- PKNCAdata(
  data.conc = conc_obj,
  data.dose = dose_obj,
  intervals = intervals
)

cat("Running PKNCA pk.nca()...\n")
results <- pk.nca(data_obj)
df      <- as.data.frame(results)

cat(sprintf("# Parameters computed: %s\n",
            paste(sort(unique(df$PPTESTCD)), collapse = ", ")))

# ---------------------------------------------------------------------------
# Reshape to wide per subject
# ---------------------------------------------------------------------------

pull_param <- function(pptestcd) {
  rows <- subset(df, PPTESTCD == pptestcd)
  rows <- rows[order(as.character(rows$subject)), ]
  setNames(rows$PPORRES, as.character(rows$subject))
}

subjects  <- sort(unique(as.character(data$subject)))
auctau    <- pull_param("auclast")   # auclast on [0, tau] == AUCtau
cmax_ss   <- pull_param("cmax")
cmin_ss   <- pull_param("cmin")
cavg_ss   <- pull_param("cav")
fluct_pct <- pull_param("deg.fluc")
swing_val <- pull_param("swing")

# ---------------------------------------------------------------------------
# Print Python dict
# ---------------------------------------------------------------------------

cat("\n# ============================================================\n")
cat("# Copy the block below into tests/validation/test_nca_ss_reference.py\n")
cat("# as _PKNCA_SS_REFERENCE\n")
cat("# ============================================================\n\n")

cat("_PKNCA_SS_REFERENCE = {\n")
for (s in subjects) {
  cat(sprintf(
    '    "%s": {\n        "AUCtau": %.6f, "Cmax_ss": %.6f, "Cmin_ss": %.6f,\n',
    s, auctau[s], cmax_ss[s], cmin_ss[s]
  ))
  cat(sprintf(
    '        "Cavg_ss": %.6f, "fluctuation_pct": %.6f, "swing": %.6f,\n    },\n',
    cavg_ss[s], fluct_pct[s], swing_val[s]
  ))
}
cat("}\n")

# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------

cat("\n# --- Human-readable summary ---\n")
cat(sprintf("%-8s %10s %10s %10s %10s %12s %10s\n",
            "Subject", "AUCtau", "Cmax_ss", "Cmin_ss", "Cavg_ss", "Fluct%", "Swing"))
cat(strrep("-", 75), "\n")
for (s in subjects) {
  cat(sprintf("%-8s %10.6f %10.6f %10.6f %10.6f %12.6f %10.6f\n",
              s, auctau[s], cmax_ss[s], cmin_ss[s],
              cavg_ss[s], fluct_pct[s], swing_val[s]))
}

stopifnot(length(subjects) == 3)
cat(sprintf("\n# All %d subjects processed successfully.\n", length(subjects)))
