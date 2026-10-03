#!/usr/bin/env Rscript
#
# disprofas_msd_crossval.R
#
# Run disprofas::mimcr() (Tsong et al. 1996 MIMCR procedure) on the
# datasets bundled with disprofas and print the time points used, the
# vessel-level data, and the reference MSD results as a Python-dictionary-
# ready block for tests/validation/test_msd_disprofas_reference.py.
#
# Usage:
#   Rscript scripts/disprofas_msd_crossval.R
#
# Requires:
#   - R >= 4.0
#   - disprofas >= 0.2.1 (install.packages("disprofas") or the GitHub source
#     at https://github.com/piusdahinden/disprofas)
#
# Reference:
#   Tsong Y, Hammerstrom T, Sathe P, Shah VP (1996). Statistical assessment
#   of mean differences between two dissolution data sets. Drug Inf J
#   30:1105-1112.
#   Dahinden P. disprofas: Non-Parametric Dissolution Profile Analysis.
#   R package (mimcr() help page, example res1).
#
# Notes:
#   mimcr() coverage is (1 - signif) * 100%, so signif = 0.10 gives the 90%
#   region used by openpkflow and signif = 0.05 reproduces the documented
#   mimcr() example. mimcr() selects time points with its `bounds` rule; the
#   selected columns (Profile.TP) are emitted so openpkflow is compared on
#   exactly the same data.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages(library(disprofas))

cases <- list(
  list(id = "dip1_type_90", data = "dip1", subset = NULL, tcol = 3:10,
       grouping = "type", ref = "R", mtad = 10, signif = 0.10),
  list(id = "dip1_type_90_mtad15", data = "dip1", subset = NULL, tcol = 3:10,
       grouping = "type", ref = "R", mtad = 15, signif = 0.10),
  list(id = "dip3_batch_95_doc_example", data = "dip3", subset = NULL, tcol = 4:6,
       grouping = "batch", ref = "blue", mtad = 10, signif = 0.05),
  list(id = "dip3_batch_90", data = "dip3", subset = NULL, tcol = 4:6,
       grouping = "batch", ref = "blue", mtad = 10, signif = 0.10),
  list(id = "dip4_type_90", data = "dip4", subset = NULL, tcol = 2:4,
       grouping = "type", ref = "ref", mtad = 10, signif = 0.10),
  list(id = "dip2_b0_b4_90", data = "dip2", subset = c("b0", "b4"), tcol = 5:8,
       grouping = "type", ref = "Reference", mtad = 10, signif = 0.10)
)

fmt <- function(x) formatC(x, digits = 15, format = "g")
rows_py <- function(m) {
  paste0("[", paste(apply(m, 1, function(r) paste0("[", paste(fmt(r), collapse = ", "), "]")),
                    collapse = ", "), "]")
}

cat(sprintf("# disprofas %s, %s\n", packageVersion("disprofas"), R.version.string))
cat("_DISPROFAS_REFERENCE = {\n")
for (case in cases) {
  data(list = case$data, package = "disprofas")
  df <- get(case$data)
  if (!is.null(case$subset)) df <- droplevels(df[df$batch %in% case$subset, ])
  res <- mimcr(data = df, tcol = case$tcol, grouping = case$grouping,
               mtad = case$mtad, signif = case$signif)
  used <- names(res$Profile.TP)
  grp <- df[[case$grouping]]
  ref <- as.matrix(df[grp == case$ref, used])
  tst <- as.matrix(df[grp != case$ref, used])
  p <- res$Parameters
  cat(sprintf("    \"%s\": {\n", case$id))
  cat(sprintf("        \"columns\": [%s],\n", paste0("\"", used, "\"", collapse = ", ")))
  cat(sprintf("        \"reference\": %s,\n", rows_py(ref)))
  cat(sprintf("        \"test\": %s,\n", rows_py(tst)))
  cat(sprintf("        \"mtad\": %s,\n", fmt(case$mtad)))
  cat(sprintf("        \"confidence_level\": %s,\n", fmt(1 - case$signif)))
  cat(sprintf("        \"dm\": %s,\n", fmt(p[["dm"]])))
  cat(sprintf("        \"f_crit\": %s,\n", fmt(p[["F.crit"]])))
  cat(sprintf("        \"sim_limit\": %s,\n", fmt(p[["Sim.Limit"]])))
  cat(sprintf("        \"obs_lower\": %s,\n", fmt(p[["Obs.L"]])))
  cat(sprintf("        \"obs_upper\": %s,\n", fmt(p[["Obs.U"]])))
  cat(sprintf("        \"similar\": %s,\n",
              if (res$Similarity[["Tsong"]] == "Similar") "True" else "False"))
  cat("    },\n")
}
cat("}\n")
