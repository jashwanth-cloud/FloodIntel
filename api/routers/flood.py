from fastapi import APIRouter, HTTPException
from api.services.flood_service import get_flood_status

router = APIRouter(prefix="/api/flood", tags=["Flood Intelligence"])


@router.get("/status", description="Get the current flood prediction summary.")
async def get_flood_status_api():
    try:
        return get_flood_status()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
