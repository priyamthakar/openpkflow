.libPaths("D:/R-library/4.6")
library(replicateBE)
data(rds07, package = "replicateBE")

d <- rds07
d$logPK <- log(d$PK)

cat("=== design check ===\n")
cat("n subjects:", length(unique(d$subject)), "\n")
print(table(d$sequence, d$treatment))

cat("\n=== GMR check (naive geometric means) ===\n")
gm_r <- exp(mean(d$logPK[d$treatment == "R"]))
gm_t <- exp(mean(d$logPK[d$treatment == "T"]))
cat("GM(R):", gm_r, " GM(T):", gm_t, " GMR (T/R):", gm_t / gm_r, "\n")

cat("\n=== CVwR via ANOVA on reference-only data ===\n")
r_only <- d[d$treatment == "R", ]
r_only$subject <- factor(r_only$subject)
r_only$sequence <- factor(r_only$sequence)
r_only$period <- factor(r_only$period)
fit <- aov(logPK ~ sequence + subject:sequence + period, data = r_only)
tbl <- summary(fit)[[1]]
print(tbl)
resid_row <- nrow(tbl)
mse <- tbl[resid_row, "Mean Sq"]
cat("\nResidual MSE (sigma_wR^2 estimate):", mse, "\n")
sigma_wr <- sqrt(mse)
cvwr <- sqrt(exp(mse) - 1) * 100
cat("sigma_wR:", sigma_wr, "\n")
cat("CVwR (%):", cvwr, "\n")

cat("\n=== simple paired-difference CVwR (subjects with exactly 2 R obs) ===\n")
agg <- split(r_only$logPK, r_only$subject)
diffs <- sapply(agg[sapply(agg, length) == 2], function(x) x[1] - x[2])
sigma_wr2 <- sqrt(sum(diffs^2) / (2 * length(diffs)))
cat("n paired subjects:", length(diffs), "\n")
cat("sigma_wR (paired-diff method):", sigma_wr2, "\n")
cat("CVwR (paired-diff method, %):", sqrt(exp(sigma_wr2^2) - 1) * 100, "\n")
