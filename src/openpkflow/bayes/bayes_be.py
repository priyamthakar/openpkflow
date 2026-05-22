"""Bayesian 2x2 crossover bioequivalence via PyMC (MCMC sampling).

Requires: pip install openpkflow[bayes]

Fits a log-scale linear mixed model with fixed effects for sequence, period,
and treatment, and a random subject-within-sequence effect. Decision quantity:
P(0.80 <= GMR <= 1.25) from the posterior. Report shows this alongside the
frequentist 90% CI so both analyses can be compared side-by-side.

Reference: Grieve AP (1985) A Bayesian analysis of the two-period crossover
design for clinical trials. Biometrics 41:979-90. DOI:10.2307/2530971
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

_BE_LO: float = 0.80
_BE_HI: float = 1.25
_MIN_SUBJECTS: int = 4


@dataclass
class BayesBEResult:
    """Posterior result from Bayesian 2x2 crossover BE analysis.

    Attributes
    ----------
    metric : str
        PK metric label (e.g. "AUC", "Cmax").
    n_subjects : int
        Number of subjects with complete paired data.
    n_samples : int
        Total posterior samples (chains x draws).
    gmr_posterior : np.ndarray
        Posterior samples of GMR = exp(beta_treatment).
    gmr_mean : float
        Posterior mean GMR.
    gmr_95ci : tuple[float, float]
        95% credible interval for GMR.
    p_be : float
        P(0.80 <= GMR <= 1.25) from posterior.
    beta_t_posterior : np.ndarray
        Posterior samples of log(GMR).
    beta_t_mean : float
        Posterior mean of log(GMR).
    beta_t_95ci : tuple[float, float]
        95% credible interval for log(GMR).
    sigma_b_mean : float
        Posterior mean between-subject log-scale SD.
    sigma_w_mean : float
        Posterior mean within-subject log-scale SD.
    freq_gmr : float
        Frequentist GMR (paired log-scale mean).
    freq_90ci : tuple[float, float]
        Frequentist 90% CI for GMR.
    freq_be : bool
        Whether frequentist 90% CI lies entirely within [0.80, 1.25].
    warnings : list[str]
        Diagnostic warnings.
    """

    metric: str
    n_subjects: int
    n_samples: int
    gmr_posterior: np.ndarray
    gmr_mean: float
    gmr_95ci: tuple[float, float]
    p_be: float
    beta_t_posterior: np.ndarray
    beta_t_mean: float
    beta_t_95ci: tuple[float, float]
    sigma_b_mean: float
    sigma_w_mean: float
    freq_gmr: float
    freq_90ci: tuple[float, float]
    freq_be: bool
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return plain-text summary of the Bayesian BE result.

        Returns
        -------
        str
            ASCII summary with decision, posterior, and frequentist comparison.
        """
        if self.p_be >= 0.95:
            decision = "PASS"
        elif self.p_be >= 0.80:
            decision = "BORDERLINE"
        else:
            decision = "FAIL"
        freq_str = "PASS" if self.freq_be else "FAIL"
        title = f"Bayesian BE -- {self.metric}"
        lines = [
            title,
            "=" * len(title),
            f"Subjects: {self.n_subjects} | MCMC samples: {self.n_samples}",
            "",
            "Bayesian Analysis:",
            f"  GMR    = {self.gmr_mean:.4g}"
            f"  [95% CrI: {self.gmr_95ci[0]:.4g}, {self.gmr_95ci[1]:.4g}]",
            f"  P(BE)  = P(0.80 <= GMR <= 1.25) = {self.p_be:.3f}  [{decision}]",
            f"  log(GMR) = {self.beta_t_mean:.4g}"
            f"  [95% CrI: {self.beta_t_95ci[0]:.4g}, {self.beta_t_95ci[1]:.4g}]",
            f"  sigma_b (between-subject) = {self.sigma_b_mean:.4g}",
            f"  sigma_w (within-subject)  = {self.sigma_w_mean:.4g}",
            "",
            "Frequentist Reference (90% CI, paired log-scale):",
            f"  GMR = {self.freq_gmr:.4g}"
            f"  [90% CI: {self.freq_90ci[0]:.4g}, {self.freq_90ci[1]:.4g}]  [{freq_str}]",
        ]
        if self.warnings:
            lines += ["", "Warnings:"] + [f"  [!] {w}" for w in self.warnings]
        lines += [
            "",
            "Disclaimer: This report was generated using OpenPKFlow (open-source).",
            "Final regulatory interpretation should be reviewed by qualified experts.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        """Return plain-dict representation without raw posterior arrays.

        Returns
        -------
        dict[str, object]
            Summary statistics and metadata as basic Python types.
        """
        return {
            "metric": self.metric,
            "n_subjects": self.n_subjects,
            "n_samples": self.n_samples,
            "gmr_mean": self.gmr_mean,
            "gmr_95ci": self.gmr_95ci,
            "p_be": self.p_be,
            "beta_t_mean": self.beta_t_mean,
            "beta_t_95ci": self.beta_t_95ci,
            "sigma_b_mean": self.sigma_b_mean,
            "sigma_w_mean": self.sigma_w_mean,
            "freq_gmr": self.freq_gmr,
            "freq_90ci": self.freq_90ci,
            "freq_be": self.freq_be,
            "warnings": self.warnings,
        }

    def report(
        self,
        output_path: str | Path | None = None,
        *,
        format: str = "html",
    ) -> str:
        """Generate a formatted report.

        Parameters
        ----------
        output_path : str or Path or None, optional
            Path to write the report file.
        format : str, optional
            "html" or "markdown".

        Returns
        -------
        str
            Rendered report content.
        """
        from openpkflow.bayes.reporting import report_bayes_be

        return report_bayes_be(self, output_path=output_path, format=format)


def _validate_be_data(data: object) -> None:
    """Validate that *data* has the required columns and constraints."""
    import pandas as pd

    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame.")
    required = {"subject", "sequence", "period", "treatment", "value"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if data["value"].astype(float).le(0).any():
        raise ValueError("All 'value' entries must be positive (log-transform requires > 0).")
    n_subj = data["subject"].nunique()
    if n_subj < _MIN_SUBJECTS:
        raise ValueError(
            f"Bayesian BE requires >= {_MIN_SUBJECTS} subjects with paired data; got {n_subj}."
        )


def _complete_pairs(data: pd.DataFrame) -> tuple[pd.DataFrame, list[object]]:
    """Return DataFrame with only subjects having exactly one T and one R observation."""

    df = data.copy()
    trt_upper = df["treatment"].astype(str).str.upper()
    df["_trt_norm"] = trt_upper.map(lambda x: "T" if x in ("T", "TEST") else "R")

    keep = []
    dropped = []
    for subj, grp in df.groupby("subject"):
        t_count = (grp["_trt_norm"] == "T").sum()
        r_count = (grp["_trt_norm"] == "R").sum()
        if t_count == 1 and r_count == 1:
            keep.append(subj)
        else:
            dropped.append(subj)
    df = df[df["subject"].isin(keep)].copy()
    df["_trt_norm"] = df["_trt_norm"]  # keep normalized column
    return df, dropped


def _frequentist_90ci(data: pd.DataFrame) -> tuple[float, tuple[float, float]]:
    """Compute frequentist GMR and 90% CI via paired log-scale differences.

    Uses a paired t-test on within-subject log(Y_T) - log(Y_R) differences.
    df = n - 1 where n is the number of complete pairs.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain columns subject, treatment, value, _trt_norm.

    Returns
    -------
    tuple[float, tuple[float, float]]
        (GMR, (lower_90ci, upper_90ci)) all on the natural scale.
    """
    from scipy.stats import t as t_dist

    df = data
    diffs: list[float] = []
    for _subj, grp in df.groupby("subject"):
        t_row = grp[grp["_trt_norm"] == "T"]
        r_row = grp[grp["_trt_norm"] == "R"]
        if len(t_row) == 1 and len(r_row) == 1:
            diffs.append(
                float(math.log(t_row["value"].iloc[0])) - float(math.log(r_row["value"].iloc[0]))
            )

    d = np.array(diffs, dtype=float)
    n = len(d)
    d_bar = float(np.mean(d))
    se = float(np.std(d, ddof=1) / math.sqrt(n))
    t_crit = float(t_dist.ppf(0.95, df=n - 1))  # 90% two-sided CI = 95th percentile one-sided
    ci_lo = d_bar - t_crit * se
    ci_hi = d_bar + t_crit * se
    return (math.exp(d_bar), (math.exp(ci_lo), math.exp(ci_hi)))


def bayes_be(
    data: object,
    *,
    metric: str = "AUC",
    n_samples: int = 2000,
    tune: int = 1000,
    chains: int = 2,
) -> BayesBEResult:
    """Bayesian 2x2 crossover bioequivalence analysis via PyMC.

    Fits a log-scale linear mixed model with fixed effects for sequence, period,
    and treatment, and a random subject-within-sequence effect using NUTS sampling.
    Decision quantity: P(0.80 <= GMR <= 1.25).

    Parameters
    ----------
    data : pd.DataFrame
        Crossover data. Required columns:

        - ``subject``: subject identifier
        - ``sequence``: "RT" or "TR" (Reference-first or Test-first)
        - ``period``: 1 or 2
        - ``treatment``: "T"/"Test" (test) or "R"/"Reference" (reference)
        - ``value``: positive PK metric (AUC or Cmax) -- log-transformed internally

    metric : str, optional
        Label for the PK metric, used in reports. Default "AUC".
    n_samples : int, optional
        MCMC draws per chain after tuning. Default 2000.
    tune : int, optional
        MCMC tuning steps per chain. Default 1000.
    chains : int, optional
        Number of independent chains. Default 2.

    Returns
    -------
    BayesBEResult
        Posterior samples, P(BE), and frequentist 90% CI for comparison.

    Raises
    ------
    ImportError
        If PyMC is not installed (pip install openpkflow[bayes]).
    TypeError
        If data is not a pandas DataFrame.
    ValueError
        If required columns are missing, values are non-positive, or fewer than
        4 subjects have complete paired data.

    References
    ----------
    Grieve AP (1985) A Bayesian analysis of the two-period crossover design
    for clinical trials. Biometrics 41:979-90. DOI:10.2307/2530971
    """
    try:
        import pymc as pm
        import pytensor.tensor as pt
    except ImportError as exc:
        raise ImportError(
            "Bayesian BE requires PyMC. Install with: pip install openpkflow[bayes]"
        ) from exc

    _validate_be_data(data)

    df, dropped = _complete_pairs(data)

    warn_list: list[str] = []
    if dropped:
        warn_list.append(
            f"Dropped {len(dropped)} subject(s) with incomplete paired data: {dropped}."
        )

    n_subj = df["subject"].nunique()
    if n_subj < _MIN_SUBJECTS:
        raise ValueError(
            f"After dropping incomplete pairs, only {n_subj} subjects remain "
            f"(minimum {_MIN_SUBJECTS})."
        )
    if n_subj < 12:
        warn_list.append(
            f"Only {n_subj} subjects. Sample sizes < 12 are typically inadequate for regulatory BE."
        )

    subjects = sorted(df["subject"].unique())
    sub_map = {s: i for i, s in enumerate(subjects)}

    sub_codes = np.array([sub_map[s] for s in df["subject"]], dtype=np.intp)
    seq_arr = (df["sequence"].astype(str).str.upper() == "TR").astype(float).values
    per_arr = (df["period"].astype(int) == 2).astype(float).values
    trt_arr = (df["_trt_norm"] == "T").astype(float).values
    log_y = np.log(df["value"].values.astype(float))

    # Frequentist 90% CI (does not require PyMC)
    freq_gmr, freq_90ci = _frequentist_90ci(df)
    freq_be = freq_90ci[0] >= _BE_LO and freq_90ci[1] <= _BE_HI

    with pm.Model():
        # Weakly informative priors on log scale
        mu = pm.Normal("mu", 0.0, 3.0)
        beta_seq = pm.Normal("beta_seq", 0.0, 1.0)
        beta_per = pm.Normal("beta_per", 0.0, 1.0)
        beta_trt = pm.Normal("beta_trt", 0.0, 0.5)

        # Non-centered subject random effects
        sigma_b = pm.HalfNormal("sigma_b", 1.0)
        u_raw = pm.Normal("u_raw", 0.0, 1.0, shape=n_subj)
        u = pm.Deterministic("u", u_raw * sigma_b)

        sigma_w = pm.HalfNormal("sigma_w", 0.5)

        mu_y = mu + beta_seq * seq_arr + beta_per * per_arr + beta_trt * trt_arr + u[sub_codes]
        pm.Normal("y_obs", mu=mu_y, sigma=sigma_w, observed=log_y)

        pm.Deterministic("gmr", pt.exp(beta_trt))

        import warnings as _w

        with _w.catch_warnings():
            _w.simplefilter("ignore")
            trace = pm.sample(
                n_samples,
                tune=tune,
                chains=chains,
                progressbar=False,
                return_inferencedata=True,
            )

    post = trace.posterior
    beta_t_samp = post["beta_trt"].values.flatten().astype(float)
    gmr_samp = post["gmr"].values.flatten().astype(float)
    sigma_b_samp = post["sigma_b"].values.flatten().astype(float)
    sigma_w_samp = post["sigma_w"].values.flatten().astype(float)

    def _ci95(arr: np.ndarray) -> tuple[float, float]:
        return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))

    p_be = float(np.mean((gmr_samp >= _BE_LO) & (gmr_samp <= _BE_HI)))

    try:
        import arviz as az

        ess = az.ess(trace)
        min_ess = float(ess["beta_trt"].values.min())
        if min_ess < 100 * chains:
            warn_list.append(
                f"Low ESS for beta_trt (ESS = {min_ess:.0f}). "
                "Consider increasing n_samples or tune."
            )
        rhat_vals = az.rhat(trace)
        max_rhat = float(rhat_vals["beta_trt"].values.max())
        if max_rhat > 1.05:
            warn_list.append(
                f"R-hat for beta_trt = {max_rhat:.3f} > 1.05. "
                "Chains may not have converged. Increase tune or n_samples."
            )
    except Exception:
        pass

    return BayesBEResult(
        metric=metric,
        n_subjects=n_subj,
        n_samples=len(beta_t_samp),
        gmr_posterior=gmr_samp,
        gmr_mean=float(np.mean(gmr_samp)),
        gmr_95ci=_ci95(gmr_samp),
        p_be=p_be,
        beta_t_posterior=beta_t_samp,
        beta_t_mean=float(np.mean(beta_t_samp)),
        beta_t_95ci=_ci95(beta_t_samp),
        sigma_b_mean=float(np.mean(sigma_b_samp)),
        sigma_w_mean=float(np.mean(sigma_w_samp)),
        freq_gmr=freq_gmr,
        freq_90ci=freq_90ci,
        freq_be=freq_be,
        warnings=warn_list,
    )
