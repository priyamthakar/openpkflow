from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import jinja2

from openpkflow import __version__
from openpkflow.dissolution.plotting import dissolution_profile_plot_b64

TEMPLATES_DIR = Path(__file__).parent / "templates"

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). "
    "Final regulatory interpretation should be reviewed by qualified "
    "formulation, pharmacokinetic, and regulatory experts."
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
    """Render a dissolution comparison HTML report.

    Parameters
    ----------
    title :
        Report title.
    reference_label :
        Label for the reference formulation.
    test_label :
        Label for the test formulation.
    f1_value :
        Computed f1 difference factor.
    f2_value :
        Computed f2 similarity factor.
    n_timepoints :
        Number of matched timepoints used in the calculation.
    time_points :
        Timepoint values for the data table.
    reference_mean :
        Mean percent dissolved values for the reference at each timepoint.
    test_mean :
        Mean percent dissolved values for the test at each timepoint.
    output_path :
        If given, write the rendered HTML to this path (parent dirs created
        automatically).

    Returns
    -------
    str
        The rendered HTML string.
    """
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
