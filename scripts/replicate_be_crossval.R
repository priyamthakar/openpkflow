#!/usr/bin/env Rscript
#
# replicate_be_crossval.R
#
# Generate scalar reference fixtures for OpenPKFlow replicate BE screening.
#
# Usage:
#   Rscript scripts/replicate_be_crossval.R
#
# Optional:
#   If PowerTOST is installed, EMA scaled limits are also computed with
#   PowerTOST::scABEL(CV, regulator = "EMA") and printed for comparison.
#
# Scope:
#   This validates scalar screening summaries only: GMR, subject-difference
#   90% CI, CVwR, EMA-style scaled limits, and FDA-style RSABE point criterion.
#   It is not a full FDA RSABE 95% upper-bound or SAS PROC MIXED parity script.

cv_to_s <- function(cv) sqrt(log(1 + cv^2))
s_to_cv_pct <- function(s) sqrt(exp(s^2) - 1) * 100

ema_limits <- function(swr, be_lower = 0.80, be_upper = 1.25) {
  cvwr <- sqrt(exp(swr^2) - 1)
  if (cvwr <= 0.30) {
    return(c(be_lower, be_upper))
  }
  capped <- min(swr, cv_to_s(0.50))
  upper <- exp(0.760 * capped)
  c(1 / upper, upper)
}

make_partial <- function(n, ratio, cv_wr) {
  swr <- cv_to_s(cv_wr)
  sequences <- c("TRR", "RTR", "RRT")
  rows <- list()
  k <- 1
  for (i in seq_len(n)) {
    subject <- sprintf("S%02d", i)
    sequence <- sequences[((i - 1) %% length(sequences)) + 1]
    base <- 100 + (i - 1)
    ref_logs <- c(log(base) - swr / sqrt(2), log(base) + swr / sqrt(2))
    test_log <- log(base * ratio)
    r_index <- 1
    for (period in seq_len(nchar(sequence))) {
      treatment <- substr(sequence, period, period)
      if (treatment == "R") {
        value <- exp(ref_logs[r_index])
        r_index <- r_index + 1
      } else {
        value <- exp(test_log)
      }
      rows[[k]] <- data.frame(
        subject = subject,
        sequence = sequence,
        period = period,
        treatment = treatment,
        value = value
      )
      k <- k + 1
    }
  }
  do.call(rbind, rows)
}

summarize_partial <- function(n, ratio, cv_wr) {
  df <- make_partial(n, ratio, cv_wr)
  df$log_value <- log(df$value)

  subject_rows <- list()
  r_ss <- 0
  r_df <- 0
  subjects <- sort(unique(df$subject))
  for (subject in subjects) {
    sub <- df[df$subject == subject, ]
    t_vals <- sub$log_value[sub$treatment == "T"]
    r_vals <- sub$log_value[sub$treatment == "R"]
    t_mean <- mean(t_vals)
    r_mean <- mean(r_vals)
    subject_rows[[length(subject_rows) + 1]] <- t_mean - r_mean
    r_ss <- r_ss + sum((r_vals - mean(r_vals))^2)
    r_df <- r_df + length(r_vals) - 1
  }

  diffs <- unlist(subject_rows)
  mean_diff <- mean(diffs)
  sd_diff <- sd(diffs)
  se <- sd_diff / sqrt(length(diffs))
  tcrit <- qt(0.95, df = length(diffs) - 1)
  swr <- sqrt(r_ss / r_df)
  limits <- ema_limits(swr)
  theta <- (log(1.25) / 0.25)^2

  list(
    n = n,
    ratio = ratio,
    cv_wr = cv_wr,
    gmr = exp(mean_diff),
    gmr_lower_90ci = exp(mean_diff - tcrit * se),
    gmr_upper_90ci = exp(mean_diff + tcrit * se),
    cv_wr_pct = s_to_cv_pct(swr),
    swr = swr,
    scaled_lower = limits[1],
    scaled_upper = limits[2],
    rsabe_point_criterion = mean_diff^2 - theta * swr^2
  )
}

scenarios <- list(
  partial_highvar = list(n = 12, ratio = 1.05, cv_wr = 0.40),
  partial_lowvar = list(n = 12, ratio = 1.00, cv_wr = 0.10),
  partial_cap = list(n = 24, ratio = 1.20, cv_wr = 0.50),
  partial_fail_point = list(n = 24, ratio = 1.30, cv_wr = 0.40)
)

cat("# ============================================================\n")
cat("# Replicate BE scalar fixture generator for OpenPKFlow\n")
cat("# Scope: screening summaries only, not full RSABE/SAS parity\n")
cat("# ============================================================\n\n")

if (requireNamespace("PowerTOST", quietly = TRUE)) {
  cat(sprintf("# PowerTOST version: %s\n", as.character(utils::packageVersion("PowerTOST"))))
  cat("# PowerTOST EMA scaled limits for comparison:\n")
  for (cv in c(0.10, 0.40, 0.50)) {
    cat(sprintf(
      "#   CV %.2f -> %s\n",
      cv,
      paste(PowerTOST::scABEL(CV = cv, regulator = "EMA"), collapse = ", ")
    ))
  }
  cat("\n")
} else {
  cat("# PowerTOST not installed; using documented EMA formula exp(+/-0.760*sWR).\n\n")
}

cat("_REPLICATE_REFERENCE = {\n")
for (name in names(scenarios)) {
  s <- scenarios[[name]]
  out <- summarize_partial(s$n, s$ratio, s$cv_wr)
  cat(sprintf('    "%s": {\n', name))
  cat(sprintf('        "n": %d,\n', out$n))
  cat(sprintf('        "ratio": %.2f,\n', out$ratio))
  cat(sprintf('        "cv_wr": %.2f,\n', out$cv_wr))
  cat(sprintf('        "gmr": %.12f,\n', out$gmr))
  cat(sprintf('        "gmr_lower_90ci": %.12f,\n', out$gmr_lower_90ci))
  cat(sprintf('        "gmr_upper_90ci": %.12f,\n', out$gmr_upper_90ci))
  cat(sprintf('        "cv_wr_pct": %.12f,\n', out$cv_wr_pct))
  cat(sprintf('        "swr": %.12f,\n', out$swr))
  cat(sprintf('        "scaled_lower": %.12f,\n', out$scaled_lower))
  cat(sprintf('        "scaled_upper": %.12f,\n', out$scaled_upper))
  cat(sprintf('        "rsabe_point_criterion": %.12f,\n', out$rsabe_point_criterion))
  cat("    },\n")
}
cat("}\n\n")
cat("# Copy the dictionary above into tests/validation/test_be_replicate_reference.py\n")
