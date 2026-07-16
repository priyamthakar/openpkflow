"""NCA endpoints."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.deps import saved_upload
from app.schemas.nca import NcaOptions, NcaResponse, SparseNcaRequest, SparseNcaResponse
from app.services.nca_service import (
    run_nca,
    run_sparse_nca,
    write_nca_report,
    write_sparse_nca_report,
)

router = APIRouter(prefix="/api/nca", tags=["nca"])

_MIME: dict[str, str] = {
    "html": "text/html",
    "markdown": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md", "pdf": ".pdf", "docx": ".docx"}


@router.post("/analyze", response_model=NcaResponse)
def analyze(
    file: UploadFile,
    options: str = Form(default="{}"),
) -> NcaResponse:
    """Run NCA on an uploaded CSV and return results + per-subject profiles."""
    opts = NcaOptions.model_validate(json.loads(options))
    with saved_upload(file) as path:
        data = run_nca(path, opts)
    return NcaResponse(**data)


@router.post("/report")
def report(
    file: UploadFile,
    options: str = Form(default="{}"),
    format: Literal["html", "markdown", "pdf", "docx"] = Form(default="html"),
) -> FileResponse:
    """Run NCA and stream the rendered report for download."""
    opts = NcaOptions.model_validate(json.loads(options))
    ext = _EXT.get(format, ".html")
    tmp_out = Path(tempfile.mktemp(suffix=ext))
    with saved_upload(file) as path:
        write_nca_report(path, opts, tmp_out, fmt=format)
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"nca_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )


@router.post("/sparse/analyze", response_model=SparseNcaResponse)
def analyze_sparse(request: SparseNcaRequest) -> SparseNcaResponse:
    """Fit the core one-compartment oral model to sparse samples."""
    _result, payload = run_sparse_nca(request)
    return SparseNcaResponse(**payload)


@router.post("/sparse/report")
def report_sparse(
    request: SparseNcaRequest,
    format: Literal["html", "markdown"] = "html",
) -> FileResponse:
    """Fit sparse samples and stream a screening report."""
    ext = ".md" if format == "markdown" else ".html"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_out = Path(tmp.name)
    write_sparse_nca_report(request, tmp_out, fmt=format)
    return FileResponse(
        path=tmp_out,
        media_type="text/markdown" if format == "markdown" else "text/html",
        filename=f"sparse_nca_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )
