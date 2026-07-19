"""SUPAC-IR and alcohol dose-dumping screening endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.supac import (
    AlcoholDosingRequest,
    AlcoholDosingResponse,
    SupacClassifyRequest,
    SupacClassifyResponse,
)
from app.services.supac_service import run_alcohol_dosing, run_supac_classify

router = APIRouter(prefix="/api/supac", tags=["supac"])


@router.post("/classify", response_model=SupacClassifyResponse)
def classify(request: SupacClassifyRequest) -> SupacClassifyResponse:
    """Screen a SUPAC-IR composition change level by excipient function."""
    return SupacClassifyResponse(**run_supac_classify(request))


@router.post("/alcohol", response_model=AlcoholDosingResponse)
def alcohol(request: AlcoholDosingRequest) -> AlcoholDosingResponse:
    """Screen alcohol dose-dumping risk via f2 vs aqueous control."""
    return AlcoholDosingResponse(**run_alcohol_dosing(request))
