"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import settings
from app.routers import be, dissolution, ivivc, nca, sim
from openpkflow import __version__ as engine_version

app = FastAPI(
    title="OpenPKFlow Web API",
    version=engine_version,
    summary="REST adapter over the openpkflow pharmacometric engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(ValueError)
async def _value_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(FileNotFoundError)
async def _file_not_found(_: Request, exc: FileNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe — also returns the engine version shown in the frontend badge."""
    return {"status": "ok", "engine_version": engine_version}


app.include_router(nca.router)
app.include_router(dissolution.router)
app.include_router(sim.router)
app.include_router(ivivc.router)
app.include_router(be.router)
