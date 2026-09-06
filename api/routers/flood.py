from fastapi import APIRouter, HTTPException

from api.services.flood_service import (
    get_flood_advisory,
    get_flood_explanation,
    get_flood_statistics,
    get_flood_status,
    get_flood_summary,
    get_flood_validation,
)


router = APIRouter(
    prefix="/api/flood",
    tags=["Flood Intelligence"],
)


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=500,
        detail="Unexpected flood service error.",
    ) from exc


@router.get("/status")
async def flood_status():
    try:
        return get_flood_status()
    except (FileNotFoundError, ValueError) as exc:
        _handle_service_error(exc)


@router.get("/summary")
async def flood_summary():
    try:
        return get_flood_summary()
    except (FileNotFoundError, ValueError) as exc:
        _handle_service_error(exc)


@router.get("/statistics")
async def flood_statistics():
    try:
        return get_flood_statistics()
    except (FileNotFoundError, ValueError) as exc:
        _handle_service_error(exc)


@router.get("/validation")
async def flood_validation():
    try:
        return get_flood_validation()
    except (FileNotFoundError, ValueError) as exc:
        _handle_service_error(exc)


@router.get("/advisory")
async def flood_advisory():
    try:
        return get_flood_advisory()
    except (FileNotFoundError, ValueError) as exc:
        _handle_service_error(exc)


@router.get("/explain")
async def flood_explain():
    try:
        return get_flood_explanation()
    except (FileNotFoundError, ValueError) as exc:
        _handle_service_error(exc)