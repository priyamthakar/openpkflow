"""Dissolution endpoints."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import FileResponse

from app.deps import saved_upload
from app.schemas.dissolution import CompareResponse, DissolutionColumns, FormulationsResponse
from app.services.dissolution_service import (
    get_formulations,
    run_compare,
    write_dissolution_report,
)

router = APIRouter(prefix="/api/dissolution", tags=["dissolution"])

_MIME: dict[str, str] = {
    "html": "text/html",
    "markdown": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md", "pdf": ".pdf", "docx": ".docx"}


@router.post("/formulations", response_model=FormulationsResponse)
def formulations(
    file: UploadFile,
    columns: str = Form(default="{}"),
) -> FormulationsResponse:
    """Return the unique formulation labels found in the CSV (for populating dropdowns)."""
    cols = DissolutionColumns.model_validate(json.loads(columns))
    with saved_upload(file) as path:
        fms = get_formulations(path, cols)
    return FormulationsResponse(formulations=fms)


@router.post("/compare", response_model=CompareResponse)
def compare(
    file: UploadFile,
    reference: str = Form(...),
    test: str = Form(...),
    columns: str = Form(default="{}"),
) -> CompareResponse:
    """Compute f1/f2 comparison between two formulations."""
    cols = DissolutionColumns.model_validate(json.loads(columns))
    with saved_upload(file) as path:
        data = run_compare(path, cols, reference, test)
    return CompareResponse(**data)


@router.post("/report")
def report(
    file: UploadFile,
    reference: str = Form(...),
    test: str = Form(...),
    columns: str = Form(default="{}"),
    format: Literal["html", "markdown", "pdf", "docx"] = Form(default="html"),
) -> FileResponse:
    """Stream the rendered dissolution comparison report."""
    from starlette.background import BackgroundTask

    cols = DissolutionColumns.model_validate(json.loads(columns))
    ext = _EXT.get(format, ".html")
    tmp_out = Path(tempfile.mktemp(suffix=ext))
    with saved_upload(file) as path:
        write_dissolution_report(path, cols, reference, test, tmp_out, fmt=format)
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"dissolution_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )
