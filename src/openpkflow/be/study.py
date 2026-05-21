"""BEStudy: high-level API for 2x2 crossover bioequivalence analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pandas as pd

from openpkflow.be.methods import be_tost
from openpkflow.be.results import BEResult

if TYPE_CHECKING:
    from openpkflow.nca.results import NCASummaryResults

_VALID_PARAMETERS = ("AUCinf", "AUClast", "Cmax")


class BEStudy:
    """2x2 crossover bioequivalence study.

    Accepts a wide-format DataFrame with one row per subject and one column each
    for reference and test PK parameter values.  The optional sequence column
    (``"RT"`` or ``"TR"``) is used for informational output only; it does not
    affect the TOST decision.

    Parameters
    ----------
    df : pd.DataFrame
        Wide-format subject data.  Required columns: *subject_col*,
        *reference_col*, *test_col*.  Optional: *sequence_col*.
    parameter : str
        Name of the PK parameter (used in output labels).
    reference_col : str, optional
        Column name for reference formulation values.  Default ``"reference"``.
    test_col : str, optional
        Column name for test formulation values.  Default ``"test"``.
    subject_col : str, optional
        Column name for subject identifiers.  Default ``"subject"``.
    sequence_col : str or None, optional
        Column name for sequence assignments (``"RT"``/``"TR"``).
        Pass ``None`` to indicate no sequence column.  Default ``"sequence"``.

    Examples
    --------
    >>> import pandas as pd
    >>> from openpkflow.be import BEStudy
    >>> df = pd.DataFrame({
    ...     "subject":  ["S1", "S2", "S3", "S4"],
    ...     "sequence": ["RT", "RT", "TR", "TR"],
    ...     "reference": [100.0, 110.0, 95.0, 105.0],
    ...     "test":      [95.0,  102.0, 92.0, 108.0],
    ... })
    >>> study = BEStudy(df, parameter="AUCinf")
    >>> result = study.analyze()
    >>> print(result.summary())
    """

    def __init__(
        self,
        df: pd.DataFrame,
        parameter: str = "AUCinf",
        *,
        reference_col: str = "reference",
        test_col: str = "test",
        subject_col: str = "subject",
        sequence_col: str | None = "sequence",
    ) -> None:
        missing = [c for c in [subject_col, reference_col, test_col] if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing!r}")
        if sequence_col is not None and sequence_col not in df.columns:
            if sequence_col != "sequence":
                raise ValueError(
                    f"sequence_col {sequence_col!r} not found in DataFrame columns. "
                    "Pass sequence_col=None if no sequence column is present."
                )
            sequence_col = None  # default 'sequence' column absent -> silently drop
        self._df = df.copy()
        self._parameter = parameter
        self._ref_col = reference_col
        self._test_col = test_col
        self._subject_col = subject_col
        self._seq_col = sequence_col

    @classmethod
    def from_nca_results(
        cls,
        reference_results: NCASummaryResults,
        test_results: NCASummaryResults,
        parameter: Literal["AUCinf", "AUClast", "Cmax"] = "AUCinf",
    ) -> BEStudy:
        """Build a BEStudy from two :class:`~openpkflow.nca.results.NCASummaryResults`.

        Run NCA separately on reference-period and test-period data, then pass
        both :class:`~openpkflow.nca.results.NCASummaryResults` here to construct
        the paired wide-format DataFrame automatically.

        Parameters
        ----------
        reference_results : NCASummaryResults
            NCA results for the reference formulation.
        test_results : NCASummaryResults
            NCA results for the test formulation.
        parameter : {"AUCinf", "AUClast", "Cmax"}, optional
            PK parameter to use for the BE analysis.  Default ``"AUCinf"``.

        Returns
        -------
        BEStudy
            Study object ready to call :meth:`analyze`.

        Raises
        ------
        ValueError
            If no subjects appear in both result sets, or if the requested
            parameter is unavailable for any subject.
        """
        if parameter not in _VALID_PARAMETERS:
            raise ValueError(
                f"parameter must be one of {_VALID_PARAMETERS!r} (got {parameter!r})."
            )

        ref_map = {r.subject: r for r in reference_results.results}
        tst_map = {t.subject: t for t in test_results.results}
        common = sorted(set(ref_map) & set(tst_map))
        if not common:
            raise ValueError(
                "No subjects are shared between reference_results and test_results."
            )

        def _extract(result: object, param: str) -> float:
            from openpkflow.nca.results import NCAResult

            r: NCAResult = result  # type: ignore[assignment]
            if param == "AUCinf":
                v = r.AUCinf_obs
            elif param == "AUClast":
                v = r.AUClast
            else:  # Cmax
                v = r.Cmax
            if v is None:
                raise ValueError(
                    f"Subject {r.subject!r} has no value for parameter {param!r}."
                )
            return float(v)

        rows = [
            {
                "subject": subj,
                "reference": _extract(ref_map[subj], parameter),
                "test": _extract(tst_map[subj], parameter),
            }
            for subj in common
        ]
        df = pd.DataFrame(rows)
        return cls(df, parameter=parameter, sequence_col=None)

    def analyze(
        self,
        *,
        be_lower: float = 0.80,
        be_upper: float = 1.25,
        alpha: float = 0.05,
    ) -> BEResult:
        """Run the TOST bioequivalence analysis.

        Parameters
        ----------
        be_lower : float, optional
            Lower acceptance limit.  Default 0.80 (FDA/EMA).
        be_upper : float, optional
            Upper acceptance limit.  Default 1.25 (FDA/EMA).
        alpha : float, optional
            One-sided significance level.  Default 0.05 (90% CI).

        Returns
        -------
        BEResult
            GMR, 90% CI, BE decision, and per-subject data table.
        """
        ref_vals = self._df[self._ref_col].astype(float).tolist()
        tst_vals = self._df[self._test_col].astype(float).tolist()

        tost = be_tost(ref_vals, tst_vals, be_lower=be_lower, be_upper=be_upper, alpha=alpha)

        subj_data: dict[str, list[object]] = {
            "subject": self._df[self._subject_col].tolist(),
            "reference": ref_vals,
            "test": tst_vals,
            "ratio": [t / r for r, t in zip(ref_vals, tst_vals, strict=True)],
            "log_diff": tost.log_diffs,
        }
        if self._seq_col is not None:
            subj_data["sequence"] = self._df[self._seq_col].tolist()
            # reorder so sequence appears early
            subj_data = {
                "subject": subj_data["subject"],
                "sequence": subj_data["sequence"],
                **{k: v for k, v in subj_data.items() if k not in ("subject", "sequence")},
            }

        subjects_df = pd.DataFrame(subj_data)

        return BEResult(
            parameter=self._parameter,
            n=tost.n,
            gmr=tost.gmr,
            gmr_lower_90ci=tost.gmr_lower_90ci,
            gmr_upper_90ci=tost.gmr_upper_90ci,
            be_lower=tost.be_lower,
            be_upper=tost.be_upper,
            bioequivalent=tost.bioequivalent,
            cv_intra_pct=tost.cv_intra_pct,
            subjects_df=subjects_df,
        )
