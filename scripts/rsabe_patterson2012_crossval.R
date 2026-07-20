.libPaths("D:/R-library/4.6")

# Table II, Patterson SD, Jones B. "Viewpoint: observations on scaled average
# bioequivalence." Pharmaceutical Statistics 2012;11(1):1-7. DOI 10.1002/pst.498.
# Partial-replicate TRR/RTR/RRT design, ni = 17 subjects/sequence, n = 51.
d <- data.frame(
  subject = c(24,25,28,29,31,34,35,39,40,44,46,48,49,50,53,54,57,
              1,2,4,5,6,7,8,9,10,11,12,13,15,16,17,18,19,
              20,22,23,26,30,32,33,36,37,38,42,43,45,47,52,55,56),
  sequence = c(rep("RRT", 17), rep("RTR", 17), rep("TRR", 17)),
  auc1 = c(449.9,192.5,568.1,735.6,307.4,292.9,217.2,368.3,193.7,102,223.6,615.8,898.4,410.4,332.4,185.2,180.6,
           812.6,338,520,400,102.1,659.3,359.8,378.4,304.5,323,176.1,218,562.4,606.8,207.5,571.3,549.7,
           124,239.7,609.6,764.4,429.1,409,271,290.8,297.2,163.8,534.1,355.1,320.5,504.5,237,246.9,235.4),
  auc2 = c(606.8,233.1,338.3,1244.2,346.6,448.5,103,446.1,255.2,245.6,349,620.9,398.3,449.4,525.3,182.1,102.9,
           1173.7,502.8,716.7,223.8,185.3,543.8,590.8,477.5,351.5,416.3,710.7,170.1,490.4,477.4,271.6,705.2,388.2,
           91.9,265.1,371.6,508.8,391.8,514.6,221,208.6,502,232.1,243.1,415.2,233.9,289.9,505,620.9,190.4),
  auc3 = c(577.2,227,403.6,641.9,369.7,267.8,127.5,222.3,244.3,286.2,507.4,665.2,828.3,442.1,293.3,194.1,117,
           889.1,398.6,860.4,173.7,42,662.9,444.3,407.9,520.2,525.1,409.5,124.6,504.7,626.8,173.7,619,141,
           59.5,433.2,432.7,449.4,335.1,406.5,463.7,489.8,334.3,434.9,441.9,334,260.5,244.2,580.6,752.2,248.4),
  cmax1 = c(32.53,21.96,110.87,50.08,87.21,18.07,18.69,52.59,29.3,22.14,27.02,60.94,164.01,59.7,39.96,18.34,9.1,
            99.85,50.48,43.86,40.05,28.76,79.04,158.86,87.84,34.35,37.07,18.94,43.15,28.35,174.94,19.18,66.63,70.06,
            9.34,38.02,199.07,74.24,31.85,30.86,86.01,38.27,49.81,34.56,136,64.55,26.35,118.91,30.55,42.2,39.15),
  cmax2 = c(118.65,22.26,50.06,181.53,90.07,21.48,17.06,48.58,21.72,9.38,20.35,26.17,25.21,102.47,42.11,21.5,12.74,
            204.09,35.15,168.78,25.17,24.83,127.92,148.97,64.57,52.26,80.9,161.34,27.71,98.5,117.31,94.92,134.69,32.15,
            11.74,16.79,52.14,35.76,74.88,70.84,41.85,40.31,66.64,16.37,33.75,34.04,37.2,49.27,63.9,106.69,13.79),
  cmax3 = c(156.33,54.16,84.6,144.26,132.92,20.87,32.01,47.24,49.27,16.3,121.92,98.08,97.02,40,38.75,9.57,18.33,
            170.94,55.71,61.04,24.48,9.27,81.8,82.4,58.01,142.92,33.62,118.89,13.11,78.22,52.18,21.39,78.1,43.11,
            18.42,83.82,72.04,36.28,19.18,65.25,79.81,20.64,25.94,29.58,35.03,41.67,24.6,35.86,40.75,115.15,62.32)
)
stopifnot(nrow(d) == 51)
write.csv(d, "tests/validation/data/be_rsabe_patterson2012_wide.csv", row.names = FALSE)

# Reshape to long: period, treatment (per Table I: TRR=T,R,R; RTR=R,T,R; RRT=R,R,T)
seq_treat <- list(TRR = c("T","R","R"), RTR = c("R","T","R"), RRT = c("R","R","T"))
long <- do.call(rbind, lapply(seq_len(nrow(d)), function(i) {
  trt <- seq_treat[[d$sequence[i]]]
  data.frame(
    subject = d$subject[i], sequence = d$sequence[i], period = 1:3, treatment = trt,
    AUC = c(d$auc1[i], d$auc2[i], d$auc3[i]),
    Cmax = c(d$cmax1[i], d$cmax2[i], d$cmax3[i])
  )
}))
write.csv(long, "tests/validation/data/be_rsabe_patterson2012_long.csv", row.names = FALSE)

analyze <- function(param) {
  cat("\n=====", param, "=====\n")
  x <- long
  x$y <- log(x[[param]])

  # method-of-moments delta: mean over subjects of (T - mean(R,R)), sign per Table I
  # for TRR: a1(T)-  (b1+c1)/2 ; RTR: b2(T) - (a2+c2)/2 ; RRT: c3(T) - (a3+b3)/2
  wide_y <- reshape(x[, c("subject","sequence","period","y")], idvar = c("subject","sequence"),
                     timevar = "period", direction = "wide")
  colnames(wide_y) <- c("subject", "sequence", "p1", "p2", "p3")
  wide_y$d <- ifelse(wide_y$sequence == "TRR", wide_y$p1 - (wide_y$p2 + wide_y$p3) / 2,
               ifelse(wide_y$sequence == "RTR", wide_y$p2 - (wide_y$p1 + wide_y$p3) / 2,
                      wide_y$p3 - (wide_y$p1 + wide_y$p2) / 2))

  n <- nrow(wide_y)
  delta_hat <- mean(wide_y$d)
  s2_d <- var(wide_y$d)
  se_delta <- sqrt(s2_d / n)
  df <- n - 3
  tcrit90 <- qt(0.95, df)
  ci_delta <- delta_hat + c(-1, 1) * tcrit90 * se_delta
  cat(sprintf("delta_hat = %.4f  90%% CI = (%.4f, %.4f)  [df=%d]\n", delta_hat, ci_delta[1], ci_delta[2], df))
  cat(sprintf("GMR = %.4f  90%% CI = (%.4f, %.4f)\n", exp(delta_hat), exp(ci_delta[1]), exp(ci_delta[2])))

  # sigma^2_WR: half the squared difference between the two R observations per subject
  r_wide <- wide_y
  r_vals <- ifelse(r_wide$sequence == "TRR", NA, NA)  # placeholder
  r1 <- ifelse(wide_y$sequence == "TRR", wide_y$p2, ifelse(wide_y$sequence == "RTR", wide_y$p1, wide_y$p1))
  r2 <- ifelse(wide_y$sequence == "TRR", wide_y$p3, ifelse(wide_y$sequence == "RTR", wide_y$p3, wide_y$p2))
  rdiff <- r1 - r2
  sigma2_wr <- sum(rdiff^2) / (2 * n)
  df_wr <- n - 3
  chi_lo <- qchisq(0.05, df_wr); chi_hi <- qchisq(0.95, df_wr)
  ci_sigma2_wr <- sort(sigma2_wr * df_wr / c(chi_hi, chi_lo))
  cat(sprintf("sigma2_WR = %.4f  90%% CI = (%.4f, %.4f)  [df=%d]\n", sigma2_wr, ci_sigma2_wr[1], ci_sigma2_wr[2], df_wr))

  theta <- (log(1.25) / 0.25)^2
  d2_point <- delta_hat^2
  d2_upper <- max(ci_delta)^2
  ts_point <- theta * sigma2_wr
  ts_upper <- theta * ci_sigma2_wr[2]
  agg_point <- d2_point - ts_point
  agg_upper <- agg_point + sqrt((d2_upper - d2_point)^2 + (ts_upper - ts_point)^2)
  cat(sprintf("delta^2 point=%.4f upper=%.4f | theta*sigma2_WR point=%.4f upper=%.4f\n",
              d2_point, d2_upper, ts_point, ts_upper))
  cat(sprintf("Aggregate criterion (delta^2 - theta*sigma2_WR): point=%.4f  95%% upper bound=%.4f\n",
              agg_point, agg_upper))
  cat(sprintf("Point estimate constraint: GMR in (0.80, 1.25)? %s\n", exp(delta_hat) > 0.80 && exp(delta_hat) < 1.25))
  cat(sprintf("SABE (FDA approach) decision: %s\n", ifelse(agg_upper < 0, "PASS", "FAIL")))
}

analyze("AUC")
analyze("Cmax")
