from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jinja2

from openpkflow import __version__
from openpkflow.dissolution.plotting import dissolution_profile_plot_b64

TEMPLATES_DIR = Path(__file__).parent / "templates"

_DISCLAIMER = (
    "This report was generated using OpenPKFlow — an open-source Python workflow "
    "for pharmacometric analysis. Final regulatory interpretation should be reviewed "
    "by qualified formulation, pharmacokinetic, and regulatory experts."
)

_FIT_DISCLAIMER = (
    "Dissolution model fitting characterises the release mechanism of a formulation — "
    "it is not a regulatory similarity test. For dissolution similarity assessment, "
    "use the f2 or bootstrap f2 method (FDA 1997 guidance)."
)


def render_html_report(
    *,
    title: str,
    reference_label: str,
    test_label: str,
    f1_value: float,
    f2_value: float,
    n_timepoints: int,
    time_points: list[float],
    reference_mean: list[float],
    test_mean: list[float],
    output_path: str | Path | None = None,
) -> str:
    """Render a dissolution comparison HTML report."""
    if f2_value >= 50:
        interpretation = (
            "f2 >= 50 supports similarity between the reference and test profiles."
        )
    else:
        interpretation = "f2 < 50 does not support similarity."

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip

    template = env.get_template("dissolution_report.html")

    rendered = template.render(
        title=title,
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        reference_label=reference_label,
        test_label=test_label,
        f1_value=f1_value,
        f2_value=f2_value,
        n_timepoints=n_timepoints,
        interpretation=interpretation,
        time_points=time_points,
        reference_mean=reference_mean,
        test_mean=test_mean,
        disclaimer=_DISCLAIMER,
        plot_b64=dissolution_profile_plot_b64(
            time_points=time_points,
            reference_mean=reference_mean,
            test_mean=test_mean,
            reference_label=reference_label,
            test_label=test_label,
        ),
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def render_model_fit_html_report(
    *,
    formulation_label: str,
    time_points: list[float],
    observed_mean: list[float],
    fit_rows: list[dict[str, Any]],
    plot_b64: str,
    output_path: str | Path | None = None,
) -> str:
    """Render a dissolution model fit HTML report."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip

    template = env.get_template("fit_report.html")

    rendered = template.render(
        title=f"Dissolution Model Fitting: {formulation_label}",
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        formulation_label=formulation_label,
        n_timepoints=len(time_points),
        time_points=time_points,
        observed_mean=observed_mean,
        fit_rows=fit_rows,
        plot_b64=plot_b64,
        disclaimer=_DISCLAIMER,
        fit_disclaimer=_FIT_DISCLAIMER,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def render_multi_media_html_report(
    *,
    title: str,
    reference_label: str,
    test_label: str,
    media_names: list[str],
    per_media_results: dict[str, dict[str, Any]],
    f2_summary: dict[str, float],
    overall_pass: bool,
    plot_b64: str,
    output_path: str | Path | None = None,
) -> str:
    """Render a multi-media dissolution HTML report."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["zip"] = zip

    template = env.get_template("multi_media_report.html")

    rendered = template.render(
        title=title,
        generated_at=datetime.now(timezone.utc).isoformat(),
        openpkflow_version=__version__,
        reference_label=reference_label,
        test_label=test_label,
        media_names=media_names,
        per_media_results=per_media_results,
        f2_summary=f2_summary,
        overall_pass=overall_pass,
        plot_b64=plot_b64,
        disclaimer=_DISCLAIMER,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered
