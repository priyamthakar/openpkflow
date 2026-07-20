"""BE endpoints."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import FileResponse

from app.deps import saved_upload
from app.schemas.be import (
    BeOptions,
    BeResponse,
    FormalBeOptions,
    FormalBeResponse,
    PowerRequest,
    PowerResponse,
    RsabeOptions,
    RsabeResponse,
    SampleSizeRequest,
    SampleSizeResponse,
)
from app.services.be_service import (
    run_be,
    run_be_power,
    run_be_sample_size,
    run_formal_be,
    run_rsabe,
    write_be_report,
    write_formal_be_report,
    write_rsabe_report,
)

router = APIRouter(prefix="/api/be", tags=["be"])

_MIME: dict[str, str] = {
    "html": "text/html",
    "markdown": "text/markdown",
}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md"}


@router.post("/analyze", response_model=BeResponse)
def analyze(
    file: UploadFile,
    options: str = Form(default="{}"),
) -> BeResponse:
    """Run bioequivalence TOST on an uploaded CSV and return results."""
    opts = BeOptions.model_validate(json.loads(options))
    with saved_upload(file) as path:
        data = run_be(path, opts)
    return BeResponse(**data)


@router.post("/report")
def report(
    file: UploadFile,
    options: str = Form(default="{}"),
    format: Literal["html", "markdown"] = Form(default="html"),
) -> FileResponse:
    """Run bioequivalence TOST and stream the rendered report for download."""
    from starlette.background import BackgroundTask

    opts = BeOptions.model_validate(json.loads(options))
    ext = _EXT.get(format, ".html")
    tmp_out = Path(tempfile.mktemp(suffix=ext))
    with saved_upload(file) as path:
        write_be_report(path, opts, tmp_out, fmt=format)
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"be_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )


@router.post("/anova/analyze", response_model=FormalBeResponse)
def analyze_anova(
    file: UploadFile,
    options: str = Form(default="{}"),
) -> FormalBeResponse:
    """Run a formal complete balanced 2x2 crossover ANOVA."""
    opts = FormalBeOptions.model_validate(json.loads(options))
    with saved_upload(file) as path:
        return FormalBeResponse(**run_formal_be(path, opts))


@router.post("/anova/report")
def report_anova(
    file: UploadFile,
    options: str = Form(default="{}"),
    format: Literal["html", "markdown"] = Form(default="html"),
) -> FileResponse:
    """Run formal ANOVA and stream the report for download."""
    from starlette.background import BackgroundTask

    opts = FormalBeOptions.model_validate(json.loads(options))
    ext = _EXT.get(format, ".html")
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_out = Path(tmp.name)
    try:
        with saved_upload(file) as path:
            write_formal_be_report(path, opts, tmp_out, fmt=format)
    except Exception:
        tmp_out.unlink(missing_ok=True)
        raise
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"formal_be_anova_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )


@router.post("/rsabe/analyze", response_model=RsabeResponse)
def analyze_rsabe(
    file: UploadFile,
    options: str = Form(default="{}"),
) -> RsabeResponse:
    """Run FDA partial-replicate (TRR/RTR/RRT) RSABE on an uploaded CSV."""
    opts = RsabeOptions.model_validate(json.loads(options))
    with saved_upload(file) as path:
        return RsabeResponse(**run_rsabe(path, opts))


@router.post("/rsabe/report")
def report_rsabe(
    file: UploadFile,
    options: str = Form(default="{}"),
    format: Literal["html", "markdown"] = Form(default="html"),
) -> FileResponse:
    """Run FDA partial-replicate RSABE and stream the report for download."""
    from starlette.background import BackgroundTask

    opts = RsabeOptions.model_validate(json.loads(options))
    ext = _EXT.get(format, ".html")
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_out = Path(tmp.name)
    try:
        with saved_upload(file) as path:
            write_rsabe_report(path, opts, tmp_out, fmt=format)
    except Exception:
        tmp_out.unlink(missing_ok=True)
        raise
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"rsabe_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )


@router.post("/power", response_model=PowerResponse)
def power(req: PowerRequest) -> PowerResponse:
    """Compute TOST power for a given GMR, CV, and sample size."""
    return PowerResponse(**run_be_power(req))


@router.post("/sample-size", response_model=SampleSizeResponse)
def sample_size(req: SampleSizeRequest) -> SampleSizeResponse:
    """Compute required sample size for a target TOST power."""
    return SampleSizeResponse(**run_be_sample_size(req))
