# Complete balanced 2x2 crossover ANOVA reference script.
#
# Model: log(value) ~ sequence + subject(sequence) + period + treatment.
# This script is intentionally independent from OpenPKFlow implementation details.
# It prints the treatment contrast, residual MSE, and ANOVA table for a supplied CSV.
#
# Usage:
# Rscript scripts/be_anova_crossval.R path/to/data.csv AUCinf

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: Rscript be_anova_crossval.R input.csv endpoint")

dat <- read.csv(args[[1]], stringsAsFactors = FALSE)
endpoint <- args[[2]]
required <- c("subject", "sequence", "period", "treatment", endpoint)
if (!all(required %in% names(dat))) stop("Missing required columns")

dat$subject <- factor(dat$subject)
dat$sequence <- factor(dat$sequence, levels = c("TR", "RT"))
dat$period <- factor(dat$period)
dat$treatment <- factor(dat$treatment, levels = c("R", "T"))
dat$log_value <- log(dat[[endpoint]])

fit <- aov(log_value ~ sequence + sequence:subject + period + treatment, data = dat)
print(summary(fit))

# The sequence effect is between subjects. Its conventional crossover denominator
# is subject nested within sequence, not the within-subject residual.
subject_means <- aggregate(log_value ~ subject + sequence, data = dat, mean)
sequence_fit <- aov(log_value ~ sequence, data = subject_means)
sequence_ss <- summary(sequence_fit)[[1]]["sequence", "Sum Sq"] * 2
subject_sequence_ss <- summary(sequence_fit)[[1]]["Residuals", "Sum Sq"] * 2
sequence_df <- summary(sequence_fit)[[1]]["sequence", "Df"]
subject_sequence_df <- summary(sequence_fit)[[1]]["Residuals", "Df"]
sequence_f <- (sequence_ss / sequence_df) / (subject_sequence_ss / subject_sequence_df)
cat(sprintf("sequence_f_subject_within_sequence=%.12f\n", sequence_f))

contrast <- coef(lm(log_value ~ treatment, data = dat))["treatmentT"]
residual_mse <- deviance(fit) / df.residual(fit)
cat(sprintf("treatment_difference=%.12f\n", contrast))
cat(sprintf("residual_mse=%.12f\n", residual_mse))
