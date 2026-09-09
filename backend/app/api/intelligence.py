from fastapi import APIRouter, HTTPException
from backend.app.services.ai.grounded_intelligence_service import GroundedIntelligenceService

router = APIRouter()
intel_service = GroundedIntelligenceService()

@router.get("/intelligence/{location_id}")
async def get_intelligence(location_id: int):
    try:
        return await intel_service.get_intelligence(location_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
