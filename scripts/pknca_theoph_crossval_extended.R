#!/usr/bin/env Rscript
#
# pknca_theoph_crossval_extended.R
#
# Extends pknca_theoph_crossval.R to cross-validate all NCA parameters that
# openpkflow computes: AUCinf_obs, AUC_percent_extrapolated, Tmax, lambda_z,
# half_life, adj_R2, n_points, CL_F (cl.obs), Vz_F (vz.obs).
#
# Usage:
#   Rscript scripts/pknca_theoph_crossval_extended.R
#
# Requires:
#   - R >= 4.0
#   - PKNCA >= 0.12.0
#   - dplyr
#
# Reference:
#   Denney WS, Duvvuri S, Buckeridge CE (2015).
#   "Simple, Automatic Noncompartmental Analysis: The PKNCA R Package."
#   Journal of Statistical Software, 59(1), 1-21. DOI: 10.18637/jss.v059.i11

suppressPackageStartupMessages({
  library(PKNCA)
  library(dplyr)
})

csv_path <- normalizePath(
  file.path(dirname(sys.frame(1)$ofile %||% "."), "..",
            "src", "openpkflow", "datasets", "theoph.csv"),
  mustWork = FALSE
)
if (!file.exists(csv_path)) {
  csv_path <- "D:/openpkflow/src/openpkflow/datasets/theoph.csv"
}

stopifnot(file.exists(csv_path))
cat(sprintf("# Dataset: %s\n", csv_path))
cat(sprintf("# PKNCA version: %s\n", as.character(packageVersion("PKNCA"))))

raw  <- read.csv(csv_path, stringsAsFactors = FALSE)
data <- raw[, c("subject", "time", "conc", "dose", "route")]
data$subject <- as.factor(data$subject)

cat(sprintf("# Subjects: %d, rows: %d\n",
            length(unique(data$subject)), nrow(data)))

# ---------------------------------------------------------------------------
# PKNCA pipeline
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

intervals <- data.frame(
  start              = 0,
  end                = Inf,
  auclast            = TRUE,
  cmax               = TRUE,
  tmax               = TRUE,
  aucinf.obs         = TRUE,
  aucpext.obs        = TRUE,
  half.life          = TRUE,
  lambda.z           = TRUE,
  adj.r.squared      = TRUE,
  lambda.z.n.points  = TRUE,
  cl.obs             = TRUE,
  vz.obs             = TRUE,
  stringsAsFactors   = FALSE
)

data_obj <- PKNCAdata(
  data.conc = conc_obj,
  data.dose = dose_obj,
  intervals = intervals
)

cat("Running PKNCA pk.nca()...\n")
results <- pk.nca(data_obj)

# ---------------------------------------------------------------------------
# Reshape to wide format
# ---------------------------------------------------------------------------

df <- as.data.frame(results)
cat(sprintf("# Parameters computed: %s\n",
            paste(sort(unique(df$PPTESTCD)), collapse = ", ")))

# Helper: pull one parameter per subject
pull_param <- function(pptestcd) {
  rows <- subset(df, PPTESTCD == pptestcd)
  rows <- rows[order(as.integer(as.character(rows$subject))), ]
  setNames(rows$PPORRES, as.character(rows$subject))
}

subjects <- as.character(sort(as.integer(levels(data$subject))))

auclast           <- pull_param("auclast")
cmax              <- pull_param("cmax")
tmax              <- pull_param("tmax")
aucinf_obs        <- pull_param("aucinf.obs")
aucpext_obs       <- pull_param("aucpext.obs")
half_life         <- pull_param("half.life")
lambda_z          <- pull_param("lambda.z")
adj_r2            <- pull_param("adj.r.squared")
lambda_z_npoints  <- pull_param("lambda.z.n.points")
cl_obs            <- pull_param("cl.obs")
vz_obs            <- pull_param("vz.obs")

# ---------------------------------------------------------------------------
# Print Python dict for test_nca_theoph_reference.py
# ---------------------------------------------------------------------------

cat("\n# ============================================================\n")
cat("# Copy the block below into tests/validation/test_nca_theoph_reference.py\n")
cat("# as _PKNCA_REFERENCE_EXTENDED\n")
cat("# ============================================================\n\n")

cat("_PKNCA_REFERENCE_EXTENDED = {\n")
for (s in subjects) {
  cat(sprintf(
    '    "%s": {\n        "AUClast": %.6f, "Cmax": %.6f, "Tmax": %.4f,\n',
    s, auclast[s], cmax[s], tmax[s]
  ))
  cat(sprintf(
    '        "AUCinf_obs": %.6f, "AUC_pct_extrap": %.4f,\n',
    aucinf_obs[s], aucpext_obs[s]
  ))
  cat(sprintf(
    '        "half_life": %.6f, "lambda_z": %.8f,\n',
    half_life[s], lambda_z[s]
  ))
  cat(sprintf(
    '        "adj_r2": %.6f, "n_points": %d,\n',
    adj_r2[s], as.integer(lambda_z_npoints[s])
  ))
  cat(sprintf(
    '        "CL_F": %.6f, "Vz_F": %.6f,\n    },\n',
    cl_obs[s], vz_obs[s]
  ))
}
cat("}\n")

# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------

cat("\n# --- Human-readable summary ---\n")
cat(sprintf("%-8s %10s %8s %8s %12s %10s %10s %10s %10s %8s %10s %10s\n",
            "Subject","AUClast","Cmax","Tmax","AUCinf_obs",
            "AUCpext%","half_life","lambda_z","adj_R2","n_pts","CL_F","Vz_F"))
cat(strrep("-", 110), "\n")
for (s in subjects) {
  cat(sprintf(
    "%-8s %10.4f %8.4f %8.4f %12.4f %10.4f %10.4f %10.6f %10.6f %8d %10.4f %10.4f\n",
    s, auclast[s], cmax[s], tmax[s], aucinf_obs[s],
    aucpext_obs[s], half_life[s], lambda_z[s],
    adj_r2[s], as.integer(lambda_z_npoints[s]),
    cl_obs[s], vz_obs[s]
  ))
}

stopifnot(length(subjects) == 12)
cat(sprintf("\n# All %d subjects processed successfully.\n", length(subjects)))
