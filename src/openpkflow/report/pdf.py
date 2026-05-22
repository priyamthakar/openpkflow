"""PDF report renderers for openpkflow using ReportLab.

Module-level imports are stdlib only. All reportlab and openpkflow imports
are deferred inside each function body to keep import cost zero when the
optional [reports] extra is not installed.
"""

from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openpkflow.nca.results import NCAResult, NCASummaryResults

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

_NAVY = "#003366"
_WHITE = "#FFFFFF"
_LIGHT_GREY = "#F2F4F7"
_DARK_TEXT = "#1A1A2E"


def render_comparison_pdf_report(
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
    """Render a dissolution comparison PDF report.

    Parameters
    ----------
    title :
        Report title string.
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
        If given, write PDF bytes to this path (parent dirs created automatically).

    Returns
    -------
    bytes
        Raw PDF bytes.
    """
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "PDF export requires reportlab. Install with: pip install openpkflow[reports]"
        ) from exc

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from openpkflow import __version__
    from openpkflow.dissolution.plotting import dissolution_profile_plot_b64

    plot_b64 = dissolution_profile_plot_b64(
        time_points=time_points,
        reference_mean=reference_mean,
        test_mean=test_mean,
        reference_label=reference_label,
        test_label=test_label,
    )

    if f2_value >= 50:
        interpretation = "f2 >= 50 supports similarity between the reference and test profiles."
    else:
        interpretation = "f2 < 50 does not support similarity."

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "PKTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor(_NAVY),
        spaceAfter=6,
    )
    style_meta = ParagraphStyle(
        "PKMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    style_heading = ParagraphStyle(
        "PKHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor(_NAVY),
        spaceBefore=14,
        spaceAfter=4,
    )
    style_disclaimer = ParagraphStyle(
        "PKDisclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
        fontName="Helvetica-Oblique",
        spaceBefore=16,
        leading=11,
    )

    navy = colors.HexColor(_NAVY)
    light_grey = colors.HexColor(_LIGHT_GREY)

    story: list[Any] = []

    story.append(Paragraph(title, style_title))
    story.append(
        Paragraph(
            f"Generated {generated_at} | OpenPKFlow v{__version__}",
            style_meta,
        )
    )

    story.append(Paragraph("Similarity Parameters", style_heading))

    params_data = [
        ["Parameter", "Value"],
        ["Reference", reference_label],
        ["Test", test_label],
        ["Timepoints", str(n_timepoints)],
        ["f1 (difference factor)", f"{f1_value:.2f}"],
        ["f2 (similarity factor)", f"{f2_value:.2f}"],
        ["Interpretation", interpretation],
    ]

    params_table = Table(params_data, colWidths=[2.5 * inch, 4.0 * inch])
    params_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(params_table)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Dissolution Profiles", style_heading))

    profile_header = [
        "Time (min)",
        f"Ref Mean % ({reference_label})",
        f"Test Mean % ({test_label})",
    ]
    profile_data = [profile_header] + [
        [f"{t:.1f}", f"{r:.2f}", f"{ts:.2f}"]
        for t, r, ts in zip(time_points, reference_mean, test_mean, strict=True)
    ]

    profile_table = Table(profile_data, colWidths=[1.8 * inch, 2.6 * inch, 2.6 * inch])
    profile_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(profile_table)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Profile Plot", style_heading))

    img_data = base64.b64decode(plot_b64)
    img_buf = io.BytesIO(img_data)
    img = Image(img_buf, width=5 * inch, height=3 * inch)
    story.append(img)

    story.append(Paragraph(_DISCLAIMER, style_disclaimer))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_model_fit_pdf_report(
    *,
    formulation_label: str,
    time_points: list[float],
    observed_mean: list[float],
    fit_rows: list[dict[str, Any]],
    plot_b64: str,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a dissolution model fit PDF report.

    Parameters
    ----------
    formulation_label :
        Label of the fitted formulation.
    time_points :
        Observed time points (minutes).
    observed_mean :
        Mean percent dissolved at each observed time point.
    fit_rows :
        Pre-processed fit data rows, one dict per model. Each dict must have:
        model_name, params, r_squared, aic, aicc, bic, n_points, n_params,
        converged, rank, is_best.
    plot_b64 :
        Base64-encoded PNG of the model fit overlay plot.
    output_path :
        If given, write PDF bytes to this path (parent dirs created automatically).

    Returns
    -------
    bytes
        Raw PDF bytes.
    """
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "PDF export requires reportlab. Install with: pip install openpkflow[reports]"
        ) from exc

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from openpkflow import __version__

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    title = f"Dissolution Model Fitting: {formulation_label}"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "PKFitTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor(_NAVY),
        spaceAfter=6,
    )
    style_meta = ParagraphStyle(
        "PKFitMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    style_heading = ParagraphStyle(
        "PKFitHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor(_NAVY),
        spaceBefore=14,
        spaceAfter=4,
    )
    style_note = ParagraphStyle(
        "PKFitNote",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        spaceBefore=4,
        leading=11,
    )
    style_disclaimer = ParagraphStyle(
        "PKFitDisclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
        fontName="Helvetica-Oblique",
        spaceBefore=10,
        leading=11,
    )

    navy = colors.HexColor(_NAVY)
    light_grey = colors.HexColor(_LIGHT_GREY)
    gold = colors.HexColor("#FFF3CD")

    converged_rows = [r for r in fit_rows if r.get("converged", False)]
    failed_rows = [r for r in fit_rows if not r.get("converged", False)]

    story: list[Any] = []

    story.append(Paragraph(title, style_title))
    story.append(
        Paragraph(
            f"Generated {generated_at} | OpenPKFlow v{__version__}",
            style_meta,
        )
    )

    story.append(Paragraph("Model Fit Summary", style_heading))

    fit_header = ["Rank", "Model", "Best", "R2", "AICc", "BIC", "Parameters"]
    fit_table_data = [fit_header]
    best_row_index: int | None = None

    for i, row in enumerate(converged_rows):
        params_str = ", ".join(
            f"{k}={v:.4g}" for k, v in row.get("params", {}).items()
        )
        r_sq = row.get("r_squared", float("nan"))
        aicc = row.get("aicc", float("nan"))
        bic = row.get("bic", float("nan"))
        rank = row.get("rank", "")
        is_best = row.get("is_best", False)
        if is_best:
            best_row_index = i + 1
        fit_table_data.append(
            [
                str(rank),
                row.get("model_name", ""),
                "Yes" if is_best else "",
                f"{r_sq:.4f}" if r_sq == r_sq else "N/A",
                f"{aicc:.2f}" if aicc == aicc else "N/A",
                f"{bic:.2f}" if bic == bic else "N/A",
                params_str,
            ]
        )

    col_widths = [
        0.5 * inch, 1.3 * inch, 0.5 * inch,
        0.65 * inch, 0.65 * inch, 0.65 * inch, 2.65 * inch,
    ]
    fit_table = Table(fit_table_data, colWidths=col_widths)

    table_style_cmds: list[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (6, 1), (6, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if best_row_index is not None:
        table_style_cmds.append(
            ("BACKGROUND", (0, best_row_index), (-1, best_row_index), gold)
        )
        table_style_cmds.append(
            ("FONTNAME", (0, best_row_index), (-1, best_row_index), "Helvetica-Bold")
        )

    fit_table.setStyle(TableStyle(table_style_cmds))
    story.append(fit_table)

    if best_row_index is not None:
        story.append(Paragraph("Highlighted row (yellow) = best model by AICc.", style_note))

    if failed_rows:
        names = ", ".join(r.get("model_name", "unknown") for r in failed_rows)
        story.append(
            Paragraph(
                f"Non-converged models (excluded from table): {names}.",
                style_note,
            )
        )

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Fit Overlay Plot", style_heading))

    img_data = base64.b64decode(plot_b64)
    img_buf = io.BytesIO(img_data)
    img = Image(img_buf, width=5 * inch, height=3 * inch)
    story.append(img)

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(_DISCLAIMER, style_disclaimer))
    story.append(Paragraph(_FIT_DISCLAIMER, style_disclaimer))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_nca_single_pdf_report(
    *,
    result: NCAResult,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a per-subject NCA PDF report.

    Parameters
    ----------
    result :
        NCA result for a single subject.
    output_path :
        If given, write PDF bytes to this path (parent dirs created automatically).

    Returns
    -------
    bytes
        Raw PDF bytes.
    """
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "PDF export requires reportlab. Install with: pip install openpkflow[reports]"
        ) from exc

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from openpkflow import __version__

    def _fmt(v: float | None) -> str:
        return f"{v:.4g}" if v is not None else "N/A"

    def _cl_label(r: NCAResult) -> tuple[str, str]:
        if r.CL_F is not None:
            return "CL_F (L/h)", _fmt(r.CL_F)
        if r.CL is not None:
            return "CL (L/h)", _fmt(r.CL)
        return "CL_F (L/h)", "N/A"

    def _vz_label(r: NCAResult) -> tuple[str, str]:
        if r.Vz_F is not None:
            return "Vz_F (L)", _fmt(r.Vz_F)
        if r.Vz is not None:
            return "Vz (L)", _fmt(r.Vz)
        return "Vz_F (L)", "N/A"

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    title = f"NCA Report - Subject {result.subject}"
    cl_lbl, cl_val = _cl_label(result)
    vz_lbl, vz_val = _vz_label(result)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "NCATitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor(_NAVY),
        spaceAfter=6,
    )
    style_meta = ParagraphStyle(
        "NCAMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    style_heading = ParagraphStyle(
        "NCAHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor(_NAVY),
        spaceBefore=14,
        spaceAfter=4,
    )
    style_warning = ParagraphStyle(
        "NCAWarning",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#856404"),
        spaceBefore=4,
        leading=12,
    )
    style_disclaimer = ParagraphStyle(
        "NCADisclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
        fontName="Helvetica-Oblique",
        spaceBefore=16,
        leading=11,
    )

    navy = colors.HexColor(_NAVY)
    light_grey = colors.HexColor(_LIGHT_GREY)

    story: list[Any] = []
    story.append(Paragraph(title, style_title))
    story.append(
        Paragraph(f"Generated {generated_at} | OpenPKFlow v{__version__}", style_meta)
    )

    story.append(Paragraph("Study Parameters", style_heading))
    study_data = [
        ["Parameter", "Value"],
        ["Subject", str(result.subject)],
        ["Route", result.route],
        ["Dose", f"{result.dose:.4g}"],
        ["AUC Method", result.auc_method],
        ["BLQ Method", result.blq_method],
    ]
    study_table = Table(study_data, colWidths=[2.5 * inch, 4.0 * inch])
    study_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(study_table)

    story.append(Paragraph("PK Parameters", style_heading))
    pk_data = [
        ["Parameter", "Value"],
        ["Cmax", _fmt(result.Cmax)],
        ["Tmax", _fmt(result.Tmax)],
        ["AUClast", _fmt(result.AUClast)],
        ["AUCinf_obs", _fmt(result.AUCinf_obs)],
        ["AUC % Extrapolated", _fmt(result.AUC_percent_extrapolated)],
        ["lambda_z", _fmt(result.lambda_z)],
        ["Half-life", _fmt(result.half_life)],
        ["lambda_z method", result.lambda_z_method or "N/A"],
        [cl_lbl, cl_val],
        [vz_lbl, vz_val],
    ]
    pk_table = Table(pk_data, colWidths=[2.5 * inch, 4.0 * inch])
    pk_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(pk_table)

    if result.warnings:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Warnings", style_heading))
        for w in result.warnings:
            story.append(Paragraph(f"- {w}", style_warning))

    story.append(Paragraph(_DISCLAIMER, style_disclaimer))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_nca_summary_pdf_report(
    *,
    summary: NCASummaryResults,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a multi-subject NCA summary PDF report.

    Parameters
    ----------
    summary :
        Collection of per-subject NCA results.
    output_path :
        If given, write PDF bytes to this path (parent dirs created automatically).

    Returns
    -------
    bytes
        Raw PDF bytes.
    """
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "PDF export requires reportlab. Install with: pip install openpkflow[reports]"
        ) from exc

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from openpkflow import __version__

    def _fmt(v: float | None) -> str:
        return f"{v:.4g}" if v is not None else "N/A"

    def _cl_val(r: NCAResult) -> str:
        if r.CL_F is not None:
            return _fmt(r.CL_F)
        if r.CL is not None:
            return _fmt(r.CL)
        return "N/A"

    def _vz_val(r: NCAResult) -> str:
        if r.Vz_F is not None:
            return _fmt(r.Vz_F)
        if r.Vz is not None:
            return _fmt(r.Vz)
        return "N/A"

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "NCASumTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor(_NAVY),
        spaceAfter=6,
    )
    style_meta = ParagraphStyle(
        "NCASumMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    style_heading = ParagraphStyle(
        "NCASumHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor(_NAVY),
        spaceBefore=14,
        spaceAfter=4,
    )
    style_disclaimer = ParagraphStyle(
        "NCASumDisclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
        fontName="Helvetica-Oblique",
        spaceBefore=16,
        leading=11,
    )

    navy = colors.HexColor(_NAVY)
    light_grey = colors.HexColor(_LIGHT_GREY)

    story: list[Any] = []
    story.append(Paragraph("NCA Summary Report", style_title))
    story.append(
        Paragraph(f"Generated {generated_at} | OpenPKFlow v{__version__}", style_meta)
    )

    if summary.study_label:
        story.append(Paragraph("Study Parameters", style_heading))
        study_data = [
            ["Parameter", "Value"],
            ["Study", summary.study_label],
            ["AUC Method", summary.auc_method],
            ["BLQ Method", summary.blq_method],
        ]
        study_table = Table(study_data, colWidths=[2.5 * inch, 4.0 * inch])
        study_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), navy),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(study_table)
        story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("PK Parameters by Subject", style_heading))

    col_headers = [
        "Subject", "AUClast", "AUCinf_obs", "AUC%Extr",
        "Cmax", "Tmax", "Half-life", "CL/CL_F", "Vz/Vz_F",
    ]
    table_data: list[list[str]] = [col_headers]
    for r in summary.results:
        table_data.append([
            str(r.subject),
            _fmt(r.AUClast),
            _fmt(r.AUCinf_obs),
            _fmt(r.AUC_percent_extrapolated),
            _fmt(r.Cmax),
            _fmt(r.Tmax),
            _fmt(r.half_life),
            _cl_val(r),
            _vz_val(r),
        ])

    col_widths = [
        0.75 * inch, 0.72 * inch, 0.78 * inch, 0.72 * inch,
        0.65 * inch, 0.60 * inch, 0.72 * inch, 0.72 * inch, 0.72 * inch,
    ]
    summary_table = Table(table_data, colWidths=col_widths)
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(summary_table)

    story.append(Paragraph(_DISCLAIMER, style_disclaimer))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


# ---------------------------------------------------------------------------
# Simulation report
# ---------------------------------------------------------------------------


def render_sim_pdf_report(
    *,
    result: Any,
    output_path: str | Path | None = None,
    time_unit: str = "h",
    conc_unit: str = "ng/mL",
) -> bytes:
    """Render a PK simulation PDF report using ReportLab.

    Parameters
    ----------
    result : SimulationResult
        Simulation result to render.
    output_path : str | Path or None, optional
        If given, write the PDF to this path.
    time_unit : str, optional
        Time unit label for tables and headings.
    conc_unit : str, optional
        Concentration unit label for tables and headings.

    Returns
    -------
    bytes
        PDF byte content.
    """
    from datetime import datetime, timezone

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from openpkflow import __version__
    from openpkflow.sim.plotting import pk_profile_plot_b64
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    report_buf = io.BytesIO()
    doc = SimpleDocTemplate(report_buf, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()
    _NAVY_COLOR = colors.HexColor(_NAVY)
    _LIGHT_GREY_COLOR = colors.HexColor(_LIGHT_GREY)

    style_h1 = ParagraphStyle("SH1", parent=styles["Heading1"],
                               textColor=_NAVY_COLOR, fontSize=16, spaceAfter=6)
    style_h2 = ParagraphStyle("SH2", parent=styles["Heading2"],
                               textColor=_NAVY_COLOR, fontSize=12, spaceAfter=4)
    style_normal = ParagraphStyle("SNorm", parent=styles["Normal"], fontSize=9)
    style_disclaimer = ParagraphStyle("SDisc", parent=styles["Normal"],
                                      fontSize=8, textColor=colors.grey)

    model_name = type(result.model).__name__
    label = result.label or "N/A"
    route = result.regimen.route
    n_doses = len(result.regimen.doses)

    _tbl_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _NAVY_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_GREY_COLOR, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])

    story: list[Any] = [
        Paragraph(f"PK Simulation Report -- {label}", style_h1),
        Paragraph(
            f"Generated: {generated_at} | OpenPKFlow v{__version__} | "
            f"Model: {model_name} | Route: {route} | Doses: {n_doses}",
            style_normal,
        ),
        Spacer(1, 6 * mm),
        Paragraph("Simulation Results", style_h2),
    ]

    metrics_data = [
        ["Metric", "Value", "Unit"],
        ["Cmax", f"{result.Cmax:.4g}", conc_unit],
        ["Tmax", f"{result.Tmax:.4g}", time_unit],
        ["Cmin", f"{min(result.concs):.4g}", conc_unit],
        ["Clast", f"{result.concs[-1]:.4g}", conc_unit],
        ["Time range", f"{result.times[0]:.4g} - {result.times[-1]:.4g}", time_unit],
    ]
    story.append(Table(metrics_data, colWidths=[60 * mm, 50 * mm, 40 * mm], style=_tbl_style))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Concentration-Time Profile", style_h2))
    b64 = pk_profile_plot_b64(
        times=result.times, concs=result.concs,
        dose_times=result.regimen.dose_times, label=result.label,
        time_unit=time_unit, conc_unit=conc_unit,
    )
    img_bytes = base64.b64decode(b64)
    story.append(Image(io.BytesIO(img_bytes), width=160 * mm, height=80 * mm))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Model Parameters", style_h2))
    params = result.model.param_dict()
    param_data = [["Parameter", "Value"]] + [
        [str(k), f"{v:.4g}" if isinstance(v, float) else str(v)]
        for k, v in params.items()
    ]
    story.append(Table(param_data, colWidths=[80 * mm, 80 * mm], style=_tbl_style))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(f"Dose Regimen ({n_doses} dose{'s' if n_doses != 1 else ''})", style_h2))
    dose_data = [["#", f"Time ({time_unit})", "Amount"]]
    for i, d in enumerate(result.regimen.doses):
        t_inf_str = f" (inf {d.t_inf:.4g} h)" if d.t_inf is not None else ""
        dose_data.append([str(i + 1), f"{d.time:.4g}", f"{d.amount:.4g}{t_inf_str}"])
    story.append(Table(dose_data, colWidths=[20 * mm, 60 * mm, 80 * mm], style=_tbl_style))

    if result.warnings:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Warnings", style_h2))
        for w in result.warnings:
            story.append(Paragraph(f"- {w}", style_normal))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(_DISCLAIMER, style_disclaimer))

    doc.build(story)
    pdf_bytes = report_buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_gof_pdf_report(
    *,
    result: object,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a population PK GOF PDF report.

    Parameters
    ----------
    result : GOFResult
        Computed GOF result.
    output_path : str | Path or None, optional
        Where to save the PDF. If None, returns bytes without saving.

    Returns
    -------
    bytes
        PDF bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from openpkflow.pop.plotting import gof_plots_b64

    report_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        report_buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    story_gof: list[Any] = []

    from reportlab.lib.styles import getSampleStyleSheet
    gof_styles = getSampleStyleSheet()
    gof_normal = gof_styles["Normal"]
    gof_disclaimer = gof_styles["Normal"]
    gof_disclaimer.fontSize = 8
    gof_h1 = gof_styles["Heading1"]
    gof_h2 = gof_styles["Heading2"]

    G_tbl = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_NAVY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D6DE")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_LIGHT_GREY)]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    title = "Population PK GOF Report"
    if result.study_label:
        title += f" -- {result.study_label}"
    story_gof.append(Paragraph(title, gof_h1))
    story_gof.append(Paragraph(
        f"Generated by OpenPKFlow | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        gof_normal,
    ))
    story_gof.append(Spacer(1, 6 * mm))

    pm = result.pred_metrics()
    im = result.ipred_metrics()
    metrics_data = [
        ["Metric", "OBS vs PRED", "OBS vs IPRED"],
        ["N", str(int(pm["n"])), str(int(im["n"]))],
        ["MPE (bias)", f"{pm['MPE']:.4g}", f"{im['MPE']:.4g}"],
        ["RMSE", f"{pm['RMSE']:.4g}", f"{im['RMSE']:.4g}"],
        ["rRMSE (%)", f"{pm['rRMSE_pct']:.2f}", f"{im['rRMSE_pct']:.2f}"],
        ["R2", f"{pm['R2']:.4f}", f"{im['R2']:.4f}"],
    ]
    story_gof.append(Paragraph("GOF Metrics", gof_h2))
    story_gof.append(
        Table(metrics_data, colWidths=[60 * mm, 55 * mm, 55 * mm], style=G_tbl)
    )
    story_gof.append(Spacer(1, 6 * mm))

    story_gof.append(Paragraph("GOF Diagnostic Plots", gof_h2))
    b64 = gof_plots_b64(result)
    img_bytes = base64.b64decode(b64)
    story_gof.append(Image(io.BytesIO(img_bytes), width=160 * mm, height=120 * mm))

    if result.warnings:
        story_gof.append(Spacer(1, 4 * mm))
        story_gof.append(Paragraph("Warnings", gof_h2))
        for w in result.warnings:
            story_gof.append(Paragraph(f"- {w}", gof_normal))

    story_gof.append(Spacer(1, 6 * mm))
    story_gof.append(Paragraph(_DISCLAIMER, gof_disclaimer))

    doc.build(story_gof)
    pdf_bytes = report_buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_vpc_pdf_report(
    *,
    result: object,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a VPC PDF report.

    Parameters
    ----------
    result : VPCResult
        Computed VPC result.
    output_path : str | Path or None, optional
        Where to save the PDF. If None, returns bytes without saving.

    Returns
    -------
    bytes
        PDF bytes.
    """
    import math

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from openpkflow.pop.plotting import vpc_plot_b64

    report_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        report_buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    story_vpc: list[Any] = []

    from reportlab.lib.styles import getSampleStyleSheet
    vpc_styles = getSampleStyleSheet()
    vpc_normal = vpc_styles["Normal"]
    vpc_disclaimer = vpc_styles["Normal"]
    vpc_disclaimer.fontSize = 8
    vpc_h1 = vpc_styles["Heading1"]
    vpc_h2 = vpc_styles["Heading2"]

    V_tbl = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_NAVY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D6DE")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_LIGHT_GREY)]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    title = "Visual Predictive Check (VPC)"
    if result.study_label:
        title += f" -- {result.study_label}"
    story_vpc.append(Paragraph(title, vpc_h1))
    story_vpc.append(Paragraph(
        f"Generated by OpenPKFlow | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        vpc_normal,
    ))
    story_vpc.append(Spacer(1, 6 * mm))

    pi = result.pi
    info_data = [
        ["Setting", "Value"],
        ["N observed", str(len(result.obs_times))],
        ["N replicates", str(result.n_replicates)],
        ["N bins", str(result.n_bins)],
        ["Percentiles", f"{pi[0]:.0f} / {pi[1]:.0f} / {pi[2]:.0f}"],
    ]
    story_vpc.append(Paragraph("VPC Settings", vpc_h2))
    story_vpc.append(Table(info_data, colWidths=[80 * mm, 90 * mm], style=V_tbl))
    story_vpc.append(Spacer(1, 6 * mm))

    story_vpc.append(Paragraph("Visual Predictive Check", vpc_h2))
    b64 = vpc_plot_b64(result)
    img_bytes = base64.b64decode(b64)
    story_vpc.append(Image(io.BytesIO(img_bytes), width=160 * mm, height=90 * mm))
    story_vpc.append(Spacer(1, 4 * mm))

    def _fv(v: float) -> str:
        return f"{v:.3g}" if not math.isnan(v) else "---"

    band_data = [[
        "Bin Mid",
        f"Obs {pi[0]:.0f}th", f"Obs {pi[1]:.0f}th", f"Obs {pi[2]:.0f}th",
        f"Sim {pi[0]:.0f}th", f"Sim {pi[1]:.0f}th", f"Sim {pi[2]:.0f}th",
    ]]
    for i, mid in enumerate(result.bin_mids):
        band_data.append([
            f"{mid:.2f}",
            _fv(result.obs_lower[i]), _fv(result.obs_median[i]), _fv(result.obs_upper[i]),
            _fv(result.sim_lower[i]), _fv(result.sim_median[i]), _fv(result.sim_upper[i]),
        ])

    story_vpc.append(Table(band_data, colWidths=[25 * mm] * 7, style=V_tbl))

    if result.warnings:
        story_vpc.append(Spacer(1, 4 * mm))
        story_vpc.append(Paragraph("Warnings", vpc_h2))
        for w in result.warnings:
            story_vpc.append(Paragraph(f"- {w}", vpc_normal))

    story_vpc.append(Spacer(1, 6 * mm))
    story_vpc.append(Paragraph(_DISCLAIMER, vpc_disclaimer))

    doc.build(story_vpc)
    pdf_bytes = report_buf.getvalue()

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)

    return pdf_bytes


def render_ivivc_pdf_report(
    *,
    result: object,
    output_path: str | Path | None = None,
) -> bytes:
    """Render an IVIVC PDF report using ReportLab.

    Parameters
    ----------
    result : IVIVCResult
        IVIVC result to render.
    output_path : str or Path or None, optional
        If given, write PDF to this path.

    Returns
    -------
    bytes
        PDF byte content.
    """
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "PDF export requires reportlab. Install with: pip install openpkflow[reports]"
        ) from exc

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from openpkflow import __version__

    lp = result.levy_plot
    pp = result.predictability
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    title = f"IVIVC Level A Report"
    if result.study_label:
        title += f" -- {result.study_label}"

    # Generate base64 plot
    import base64 as _b64
    import io as _io
    import matplotlib as _mpl
    _mpl.use("Agg")
    import matplotlib.pyplot as _plt
    import numpy as _np

    fig, axes = _plt.subplots(2, 2, figsize=(8, 6), dpi=200)
    ax = axes[0, 0]
    ax.plot(result.times, result.fa, "o-", color="#003366", linewidth=2, markersize=4)
    ax.plot(result.ivt_times, result.ivt_fraction, "s--", color="#cc3300", linewidth=1, markersize=3, label="In vitro")
    ax.set_title("Fraction Absorbed vs Dissolved", fontsize=9)
    ax.set_xlabel("Time (h)", fontsize=8)
    ax.set_ylabel("Fraction", fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    ax = axes[0, 1]
    ax.scatter(lp["x"], lp["y"], color="#003366", s=20, zorder=3)
    if len(lp.get("x", [])) > 1:
        x_line = _np.linspace(0, 1, 100)
        y_line = lp["slope"] * x_line + lp["intercept"]
        ax.plot(x_line, y_line, "-", color="#cc3300", linewidth=1, label=f"R2={lp['r_squared']:.3f}")
        ax.plot([0, 1], [0, 1], ":", color="#888888", linewidth=1, label="1:1")
    ax.set_title("Levy Plot", fontsize=9)
    ax.set_xlabel("In vitro F_d", fontsize=8)
    ax.set_ylabel("In vivo F_a", fontsize=8)
    ax.legend(fontsize=6)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax = axes[1, 0]
    ax.plot(result.times, result.concentrations, "o-", color="#003366", linewidth=2, markersize=4, label="Observed")
    ax.plot(result.predicted_times, result.predicted_concs, "--", color="#cc3300", linewidth=1, label="Predicted")
    ax.set_title("Predicted vs Observed", fontsize=9)
    ax.set_xlabel("Time (h)", fontsize=8)
    ax.set_ylabel("Concentration", fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax = axes[1, 1]
    ax.plot(result.ivt_times, result.ivt_fraction * 100, "o-", color="#006699", linewidth=2, markersize=4)
    ax.set_title("Dissolution Profile", fontsize=9)
    ax.set_xlabel("Time (min)", fontsize=8)
    ax.set_ylabel("% Dissolved", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)
    fig.tight_layout()
    plot_buf = _io.BytesIO()
    fig.savefig(plot_buf, format="png", bbox_inches="tight", dpi=200)
    _plt.close(fig)
    plot_buf.seek(0)
    plot_b64 = _b64.b64encode(plot_buf.read()).decode("utf-8")

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle("IVIVCTitle", parent=styles["Title"], fontSize=18,
                                  textColor=colors.HexColor(_NAVY), spaceAfter=6)
    style_meta = ParagraphStyle("IVIVCMeta", parent=styles["Normal"], fontSize=9,
                                 textColor=colors.HexColor("#555555"), spaceAfter=12)
    style_heading = ParagraphStyle("IVIVCHeading", parent=styles["Heading2"], fontSize=12,
                                    textColor=colors.HexColor(_NAVY), spaceBefore=14, spaceAfter=4)
    style_disclaimer = ParagraphStyle("IVIVCDisc", parent=styles["Normal"], fontSize=8,
                                       textColor=colors.HexColor("#666666"),
                                       fontName="Helvetica-Oblique", spaceBefore=16, leading=11)
    navy = colors.HexColor(_NAVY)
    light_grey = colors.HexColor(_LIGHT_GREY)
    _tbl = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])

    story: list[Any] = []
    story.append(Paragraph(title, style_title))
    story.append(Paragraph(f"Generated {generated_at} | OpenPKFlow v{__version__}", style_meta))
    story.append(Paragraph("Predictability Assessment (FDA 1997)", style_heading))
    overall = "PASS" if pp.get("overall_pass", False) else "FAIL"
    pp_data = [
        ["Metric", "Value", "Criterion", "Status"],
        ["Cmax %PE", f"{pp.get('%PE_Cmax', 0):.2f}%", "<= 15%", "PASS" if pp.get("passes_cmax", False) else "FAIL"],
        ["AUCinf %PE", f"{pp.get('%PE_AUC', 0):.2f}%", "<= 15%", "PASS" if pp.get("passes_auc", False) else "FAIL"],
        ["Mean abs %PE", f"{pp.get('mean_abs_%PE', 0):.2f}%", "<= 10%", "PASS" if pp.get("passes_mean", False) else "FAIL"],
        ["Overall", "", "", overall],
    ]
    story.append(Table(pp_data, colWidths=[1.8*inch, 1.4*inch, 1.4*inch, 1.4*inch], style=_tbl))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("IVIVC Plots", style_heading))
    img_data = _b64.b64decode(plot_b64)
    img = Image(_io.BytesIO(img_data), width=5.5*inch, height=4*inch)
    story.append(img)
    story.append(Paragraph("Levy Plot Regression", style_heading))
    levy_data = [
        ["Metric", "Value"],
        ["Slope", f"{lp.get('slope', 0):.4f}"],
        ["Intercept", f"{lp.get('intercept', 0):.4f}"],
        ["R-squared", f"{lp.get('r_squared', 0):.4f}"],
        ["N (0.05-0.95)", str(len(lp.get("x", [])))],
    ]
    story.append(Table(levy_data, colWidths=[2.5*inch, 3.5*inch], style=_tbl))
    story.append(Paragraph(_DISCLAIMER, style_disclaimer))
    doc.build(story)
    pdf_bytes = buf.getvalue()
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf_bytes)
    return pdf_bytes
