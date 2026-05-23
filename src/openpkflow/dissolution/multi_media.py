"""Multi-media dissolution comparison (ICH M13A/B, SUPAC-IR)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from openpkflow.dissolution.study import ComparisonResult, DissolutionStudy

if TYPE_CHECKING:
    from matplotlib.figure import Figure


@dataclass
class MultiMediaResult:
    """Multi-media dissolution comparison results.

    Contains per-medium ComparisonResult objects and provides aggregate
    summary, reporting, and plotting.
    """

    reference_label: str
    test_label: str
    media_names: list[str] = field(default_factory=list)
    per_media_results: dict[str, ComparisonResult] = field(default_factory=dict)

    @property
    def f2_summary(self) -> dict[str, float]:
        return {m: r.f2_value for m, r in self.per_media_results.items()}

    @property
    def overall_pass(self) -> bool:
        return all(v >= 50.0 for v in self.f2_summary.values())

    def summary(self) -> str:
        lines = [
            "Multi-Media Dissolution Comparison",
            f"{'=' * 40}",
            f"Reference: {self.reference_label}",
            f"Test:      {self.test_label}",
            f"Media:     {', '.join(self.media_names)}",
            "",
            f"{'Medium':<12} {'f2':>8}  {'Status'}",
            f"{'-' * 12} {'-' * 8}  {'-' * 8}",
        ]
        for medium in self.media_names:
            if medium in self.per_media_results:
                f2 = self.per_media_results[medium].f2_value
                status = "PASS" if f2 >= 50.0 else "FAIL"
                lines.append(f"{medium:<12} {f2:>8.2f}  {status}")
        lines.append("")
        lines.append(f"Overall: {'PASS' if self.overall_pass else 'FAIL'}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_label": self.reference_label,
            "test_label": self.test_label,
            "media_names": self.media_names,
            "per_media_results": {m: r.to_dict() for m, r in self.per_media_results.items()},
            "f2_summary": self.f2_summary,
            "overall_pass": self.overall_pass,
        }

    def plot(self, output_path: str | Path | None = None, show: bool = False) -> None:
        _multi_media_plot(self.media_names, self.per_media_results, output_path, show)

    def report(
        self, output_path: str | Path, format: Literal["html", "pdf", "docx"] = "html"
    ) -> str | bytes:
        from openpkflow.dissolution.reporting import report_multi_media

        return report_multi_media(
            title="Multi-Media Dissolution Analysis",
            reference_label=self.reference_label,
            test_label=self.test_label,
            media_names=self.media_names,
            per_media_results={m: r.to_dict() for m, r in self.per_media_results.items()},
            f2_summary=self.f2_summary,
            overall_pass=self.overall_pass,
            plot_b64=self._plot_b64(),
            output_path=output_path,
            format=format,
        )

    def _plot_b64(self) -> str:
        import base64
        import io

        fig = _build_multi_media_figure(self.media_names, self.per_media_results)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=600, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()


def _build_multi_media_figure(
    media_names: list[str],
    per_media_results: dict[str, ComparisonResult],
) -> Figure:
    n = len(media_names)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 4), squeeze=False)

    for i, medium in enumerate(media_names):
        ax = axes[0, i]
        cr = per_media_results.get(medium)
        if cr is None:
            ax.set_title(f"{medium}\n(no data)")
            ax.axis("off")
            continue

        t = np.array(cr.time_points)
        r = np.array(cr.reference_mean)
        ts = np.array(cr.test_mean)

        ax.plot(t, r, "o-", color="#1f77b4", linewidth=1.5, markersize=4, label="Reference")
        ax.plot(t, ts, "s--", color="#d62728", linewidth=1.5, markersize=4, label="Test")
        ax.axhline(y=85, color="gray", linestyle=":", linewidth=0.75)

        f2 = cr.f2_value
        status = "PASS" if f2 >= 50 else "FAIL"
        color = "#2d7d46" if f2 >= 50 else "#c0392b"
        ax.set_title(
            f"{medium}\nf2={f2:.1f} [{status}]", fontsize=10, fontweight="bold", color=color
        )
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("% Released")
        ax.legend(fontsize=8, loc="lower right")
        ax.set_ylim(-2, 105)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def _multi_media_plot(
    media_names: list[str],
    per_media_results: dict[str, ComparisonResult],
    output_path: str | Path | None = None,
    show: bool = False,
) -> None:
    fig = _build_multi_media_figure(media_names, per_media_results)
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
    if show:
        plt.show(block=False)
    if not output_path and not show:
        plt.close(fig)


class MultiMediaStudy:
    """Orchestrates dissolution comparison across multiple media conditions.

    Each CSV file should contain the same ``reference_label`` and ``test_label``
    formulations.  A ``DissolutionStudy`` is created per medium; ``run()`` calls
    ``compare()`` on each and collects the results into a ``MultiMediaResult``.

    Parameters
    ----------
    media_csvs : dict[str, str | Path]
        Mapping of medium name to CSV file path.
    reference_label : str
        Formulation label for the reference product (must exist in all CSVs).
    test_label : str
        Formulation label for the test product (must exist in all CSVs).

    Examples
    --------
    >>> mm = MultiMediaStudy({"pH 1.2": "ph1.csv", "pH 4.5": "ph4.csv", "pH 6.8": "ph6.csv"})
    >>> result = mm.run()
    >>> print(result.summary())
    >>> result.report("mm_report.html")
    """

    def __init__(
        self,
        media_csvs: dict[str, str | Path],
        reference_label: str = "reference",
        test_label: str = "test",
    ) -> None:
        if len(media_csvs) < 2:
            raise ValueError("At least 2 media conditions are required")
        self._reference_label = reference_label
        self._test_label = test_label
        self._media_names: list[str] = []
        self._studies: dict[str, DissolutionStudy] = {}

        # Build a study per medium; validate labels exist
        for medium, csv_path in media_csvs.items():
            study = DissolutionStudy.from_csv(csv_path)
            formulations = study.formulations()
            if reference_label not in formulations:
                raise ValueError(
                    f"Reference formulation '{reference_label}' not found in medium '{medium}'"
                )
            if test_label not in formulations:
                raise ValueError(f"Test formulation '{test_label}' not found in medium '{medium}'")
            self._media_names.append(medium)
            self._studies[medium] = study

    @classmethod
    def from_csvs(
        cls,
        media_csvs: dict[str, str | Path],
        reference_label: str = "reference",
        test_label: str = "test",
    ) -> MultiMediaStudy:
        return cls(media_csvs, reference_label, test_label)

    @property
    def media_names(self) -> list[str]:
        return self._media_names

    def run(self) -> MultiMediaResult:
        per_media: dict[str, ComparisonResult] = {}
        for medium in self._media_names:
            study = self._studies[medium]
            per_media[medium] = study.compare(self._reference_label, self._test_label)
        return MultiMediaResult(
            reference_label=self._reference_label,
            test_label=self._test_label,
            media_names=self._media_names,
            per_media_results=per_media,
        )
