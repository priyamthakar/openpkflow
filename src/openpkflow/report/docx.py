"""Word document report renderers for openpkflow dissolution reports."""

from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). "
    "Final regulatory interpretation should be reviewed by qualified "
    "formulation, pharmacokinetic, and regulatory experts."
)

_FIT_DISCLAIMER = (
    "Dissolution model fitting characterises the release mechanism of a "
    "formulation. It is not a regulatory similarity test. Use f2 or bootstrap "
    "f2 for dissolution similarity assessment."
)


def render_comparison_docx_report(
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
) -> bytes:
    """Render a dissolution comparison report as a Word document.

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
        Timepoint values used in the comparison.
    reference_mean :
        Mean percent dissolved values for the reference at each timepoint.
    test_mean :
        Mean percent dissolved values for the test at each timepoint.
    output_path :
        If given, write the DOCX bytes to this path (parent dirs created
        automatically).

    Returns
    -------
    bytes
        DOCX file contents as bytes.
    """
    try:
        import docx  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Word export requires python-docx. Install with: pip install openpkflow[reports]"
        ) from exc

    from docx import Document
    from docx.shared import Inches, Pt

    from openpkflow import __version__
    from openpkflow.dissolution.plotting import dissolution_profile_plot_b64

    if f2_value >= 50:
        interpretation = "f2 >= 50 supports similarity between the reference and test profiles."
    else:
        interpretation = "f2 < 50 does not support similarity."

    plot_b64 = dissolution_profile_plot_b64(
        time_points=time_points,
        reference_mean=reference_mean,
        test_mean=test_mean,
        reference_label=reference_label,
        test_label=test_label,
    )

    document = Document()

    document.add_heading(title, level=1)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta_para = document.add_paragraph(
        f"Generated: {generated_at}  |  OpenPKFlow v{__version__}"
    )
    meta_para.runs[0].font.size = Pt(9)

    document.add_heading("Summary", level=2)

    table = document.add_table(rows=1, cols=2)
    table.style = "Table Grid"

    hdr_cells = table.rows[0].cells
    for i, heading in enumerate(["Parameter", "Value"]):
        hdr_cells[i].text = heading
    for cell in hdr_cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True

    summary_rows = [
        ("Reference", reference_label),
        ("Test", test_label),
        ("Timepoints", str(n_timepoints)),
        ("f1 (difference factor)", f"{f1_value:.2f}"),
        ("f2 (similarity factor)", f"{f2_value:.2f}"),
        ("Interpretation", interpretation),
    ]
    for label, value in summary_rows:
        row_cells = table.add_row().cells
        row_cells[0].text = label
        row_cells[1].text = value

    document.add_heading("Dissolution Profile", level=2)

    img_data = base64.b64decode(plot_b64)
    img_buf = io.BytesIO(img_data)
    document.add_picture(img_buf, width=Inches(5))

    document.add_heading("Data Table", level=2)

    data_table = document.add_table(rows=1, cols=3)
    data_table.style = "Table Grid"

    data_hdr_cells = data_table.rows[0].cells
    for i, heading in enumerate(["Time (min)", reference_label, test_label]):
        data_hdr_cells[i].text = heading
    for cell in data_hdr_cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True

    for tp, ref, tst in zip(time_points, reference_mean, test_mean, strict=True):
        row_cells = data_table.add_row().cells
        row_cells[0].text = str(tp)
        row_cells[1].text = f"{ref:.2f}"
        row_cells[2].text = f"{tst:.2f}"

    document.add_paragraph()

    disclaimer_para = document.add_paragraph(_DISCLAIMER)
    for run in disclaimer_para.runs:
        run.italic = True
        run.font.size = Pt(9)

    buf = io.BytesIO()
    document.save(buf)
    docx_bytes = buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(docx_bytes)

    return docx_bytes


def render_model_fit_docx_report(
    *,
    formulation_label: str,
    time_points: list[float],
    observed_mean: list[float],
    fit_rows: list[dict[str, Any]],
    plot_b64: str,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a dissolution model fit report as a Word document.

    Parameters
    ----------
    formulation_label :
        Label of the fitted formulation.
    time_points :
        Observed time points (minutes).
    observed_mean :
        Mean percent dissolved at each observed time point.
    fit_rows :
        Pre-processed fit data rows (one dict per model). Each dict must have:
        ``model_name``, ``params``, ``r_squared``, ``aic``, ``aicc``, ``bic``,
        ``n_points``, ``n_params``, ``converged``, ``rank``, ``is_best``.
    plot_b64 :
        Base64-encoded PNG of the model fit overlay plot.
    output_path :
        If given, write the DOCX bytes to this path (parent dirs created
        automatically).

    Returns
    -------
    bytes
        DOCX file contents as bytes.
    """
    try:
        import docx  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Word export requires python-docx. Install with: pip install openpkflow[reports]"
        ) from exc

    from docx import Document
    from docx.shared import Inches, Pt

    from openpkflow import __version__

    def _fmt_params(params: dict[str, Any]) -> str:
        return ", ".join(f"{k}={v:.4g}" for k, v in params.items())

    converged_rows = sorted(
        [r for r in fit_rows if r.get("converged", False)],
        key=lambda r: r.get("rank", 9999),
    )
    failed_rows = [r for r in fit_rows if not r.get("converged", False)]

    title = f"Dissolution Model Fitting: {formulation_label}"
    document = Document()

    document.add_heading(title, level=1)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta_para = document.add_paragraph(
        f"Generated: {generated_at}  |  OpenPKFlow v{__version__}"
    )
    meta_para.runs[0].font.size = Pt(9)

    document.add_heading("Model Fit Results", level=2)

    if converged_rows:
        table = document.add_table(rows=1, cols=6)
        table.style = "Table Grid"

        hdr_cells = table.rows[0].cells
        for i, heading in enumerate(["Rank", "Model", "R²", "AICc", "BIC", "Params"]):
            hdr_cells[i].text = heading
        for cell in hdr_cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True

        for row in converged_rows:
            row_cells = table.add_row().cells
            row_cells[0].text = str(row.get("rank", ""))
            row_cells[1].text = str(row.get("model_name", ""))
            row_cells[2].text = f"{row.get('r_squared', float('nan')):.4f}"
            row_cells[3].text = f"{row.get('aicc', float('nan')):.2f}"
            row_cells[4].text = f"{row.get('bic', float('nan')):.2f}"
            row_cells[5].text = _fmt_params(row.get("params", {}))
            if row.get("is_best", False):
                for cell in row_cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.bold = True
    else:
        document.add_paragraph("No models converged successfully.")

    if failed_rows:
        failed_names = ", ".join(r.get("model_name", "unknown") for r in failed_rows)
        failed_para = document.add_paragraph(f"Failed to converge: {failed_names}")
        failed_para.runs[0].font.size = Pt(9)
        failed_para.runs[0].italic = True

    document.add_heading("Fit Overlay Plot", level=2)

    img_data = base64.b64decode(plot_b64)
    img_buf = io.BytesIO(img_data)
    document.add_picture(img_buf, width=Inches(5))

    document.add_heading("Observed Data", level=2)

    data_table = document.add_table(rows=1, cols=2)
    data_table.style = "Table Grid"

    data_hdr_cells = data_table.rows[0].cells
    for i, heading in enumerate(["Time (min)", "Mean % Dissolved"]):
        data_hdr_cells[i].text = heading
    for cell in data_hdr_cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True

    for tp, obs in zip(time_points, observed_mean, strict=True):
        row_cells = data_table.add_row().cells
        row_cells[0].text = str(tp)
        row_cells[1].text = f"{obs:.2f}"

    document.add_paragraph()

    disclaimer_para = document.add_paragraph(_DISCLAIMER)
    for run in disclaimer_para.runs:
        run.italic = True
        run.font.size = Pt(9)

    fit_disclaimer_para = document.add_paragraph(_FIT_DISCLAIMER)
    for run in fit_disclaimer_para.runs:
        run.italic = True
        run.font.size = Pt(9)

    buf = io.BytesIO()
    document.save(buf)
    docx_bytes = buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(docx_bytes)

    return docx_bytes
