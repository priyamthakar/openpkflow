#!/usr/bin/env Rscript

# Independent sparse 1-cmt oral fit on subject 1 of R nlme::Theoph.
# Reference implementation: R 4.6.0 stats::nls, algorithm = "port".

args <- commandArgs(trailingOnly = TRUE)
csv_path <- if (length(args) >= 1) {
  args[1]
} else {
  file.path("src", "openpkflow", "datasets", "theoph.csv")
}

data <- read.csv(csv_path, stringsAsFactors = FALSE)
sparse_times <- c(0.25, 1.12, 3.82, 9.05, 24.37)
profile <- subset(data, subject == 1 & time %in% sparse_times)
dose <- 320

fit <- nls(
  conc ~ dose * ka / (Vz_F * (ka - CL_F / Vz_F)) *
    (exp(-(CL_F / Vz_F) * time) - exp(-ka * time)),
  data = profile,
  start = list(CL_F = 3, Vz_F = 30, ka = 2),
  algorithm = "port",
  lower = c(CL_F = 0.01, Vz_F = 0.1, ka = 0.01),
  upper = c(CL_F = 1000, Vz_F = 10000, ka = 10),
  control = nls.control(maxiter = 200, tol = 1e-10, minFactor = 1e-10)
)

cat("# R stats::nls reference on nlme::Theoph subject 1\n")
cat(sprintf("CL_F = %.15f\n", coef(fit)[["CL_F"]]))
cat(sprintf("Vz_F = %.15f\n", coef(fit)[["Vz_F"]]))
cat(sprintf("ka = %.15f\n", coef(fit)[["ka"]]))
cat("fitted = c(", paste(sprintf("%.15f", predict(fit)), collapse = ", "), ")\n", sep = "")
