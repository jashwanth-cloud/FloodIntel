from fastapi import APIRouter, HTTPException
from backend.app.services.alert_service import AlertEngineService

router = APIRouter()
alert_service = AlertEngineService()

@router.get("/alerts/{location_id}")
async def get_alert(location_id: int):
    try:
        return await alert_service.get_alert(location_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
