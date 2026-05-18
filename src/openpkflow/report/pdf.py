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
from typing import Any

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
