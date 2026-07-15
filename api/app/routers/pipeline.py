"""Study-pipeline endpoints."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.deps import saved_upload
from app.schemas.pipeline import PipelineOptions, PipelineResponse
from app.services.pipeline_service import run_pipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@contextmanager
def _saved_inputs(
    dissolution_file: UploadFile | None,
    nca_file: UploadFile | None,
    be_file: UploadFile | None,
) -> Iterator[tuple[dict[str, Path | None], dict[str, str]]]:
    with ExitStack() as stack:
        uploads = {
            "dissolution_csv": dissolution_file,
            "nca_csv": nca_file,
            "be_csv": be_file,
        }
        paths: dict[str, Path | None] = {}
        names: dict[str, str] = {}
        for key, upload in uploads.items():
            paths[key] = stack.enter_context(saved_upload(upload)) if upload else None
            if upload is not None:
                names[key] = upload.filename or f"{key}.csv"
        yield paths, names


def _temp_path(suffix: str) -> Path:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        return Path(tmp.name)


@router.post("/analyze", response_model=PipelineResponse)
def analyze(
    options: str = Form(default="{}"),
    dissolution_file: UploadFile | None = File(default=None),
    nca_file: UploadFile | None = File(default=None),
    be_file: UploadFile | None = File(default=None),
) -> PipelineResponse:
    """Run all uploaded study stages and return unified results."""
    opts = PipelineOptions.model_validate(json.loads(options))
    with _saved_inputs(dissolution_file, nca_file, be_file) as (paths, names):
        _result, payload = run_pipeline(
            dissolution_path=paths["dissolution_csv"],
            nca_path=paths["nca_csv"],
            be_path=paths["be_csv"],
            input_names=names,
            options=opts,
        )
    return PipelineResponse(**payload)


@router.post("/report")
def report(
    options: str = Form(default="{}"),
    format: Literal["html", "markdown"] = Form(default="html"),
    dissolution_file: UploadFile | None = File(default=None),
    nca_file: UploadFile | None = File(default=None),
    be_file: UploadFile | None = File(default=None),
) -> FileResponse:
    """Run uploaded stages and stream a unified report."""
    opts = PipelineOptions.model_validate(json.loads(options))
    suffix = ".md" if format == "markdown" else ".html"
    out = _temp_path(suffix)
    with _saved_inputs(dissolution_file, nca_file, be_file) as (paths, names):
        result, _payload = run_pipeline(
            dissolution_path=paths["dissolution_csv"],
            nca_path=paths["nca_csv"],
            be_path=paths["be_csv"],
            input_names=names,
            options=opts,
        )
        result.report(out)
    return FileResponse(
        path=out,
        media_type="text/markdown" if format == "markdown" else "text/html",
        filename=f"study_pipeline_report{suffix}",
        background=BackgroundTask(out.unlink, missing_ok=True),
    )


@router.post("/audit-bundle")
def audit_bundle(
    options: str = Form(default="{}"),
    dissolution_file: UploadFile | None = File(default=None),
    nca_file: UploadFile | None = File(default=None),
    be_file: UploadFile | None = File(default=None),
) -> FileResponse:
    """Run uploaded stages and stream a reproducibility ZIP."""
    opts = PipelineOptions.model_validate(json.loads(options))
    out = _temp_path(".zip")
    with _saved_inputs(dissolution_file, nca_file, be_file) as (paths, names):
        result, _payload = run_pipeline(
            dissolution_path=paths["dissolution_csv"],
            nca_path=paths["nca_csv"],
            be_path=paths["be_csv"],
            input_names=names,
            options=opts,
        )
        result.audit_bundle(out)
    return FileResponse(
        path=out,
        media_type="application/zip",
        filename="openpkflow_audit_bundle.zip",
        background=BackgroundTask(out.unlink, missing_ok=True),
    )
