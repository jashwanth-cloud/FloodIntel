from typing import Dict, Any, List
from backend.app.services.ai.providers.ollama_provider import OllamaAIProvider
from backend.app.services.alert_service import AlertEngineService
from backend.app.schemas.intelligence_schema import IntelligenceSchema
from datetime import datetime, timezone

class GroundedIntelligenceService:
    def __init__(self):
        self.ai_provider = OllamaAIProvider()
        self.alert_service = AlertEngineService()
        
    async def get_intelligence(self, location_id: int) -> Dict[str, Any]:
        # 1. Collect deterministic evidence
        alert = await self.alert_service.get_alert(location_id)
        
        context = {
            "location_id": location_id,
            "alert": alert,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 2. Check if AI is available
        if await self.ai_provider.health_check():
            ai_response = await self.ai_provider.generate_intelligence(context)
            if ai_response["status"] == "AVAILABLE":
                # In production, parse structured AI output here.
                # For now, return structured intelligence response.
                return IntelligenceSchema.create_intelligence_response(
                    summary=ai_response["text"],
                    severity=alert["alert_level"],
                    findings=["Based on aggregated intelligence signals."],
                    reasoning=[alert["primary_reason"]],
                    actions=[alert["recommended_action"]],
                    data_state=alert["data_state"],
                    sources=[f["source"] for f in alert["contributing_factors"]],
                    limitations=["AI-generated explanation, grounded in FloodIntel signals."],
                    uncertainty=["Confidence not directly provided by upstream models."]
                )

        # 3. Deterministic Fallback
        return IntelligenceSchema.create_intelligence_response(
            summary=f"AI unavailable. Deterministic alert: {alert['alert_level']} - {alert['primary_reason']}",
            severity=alert["alert_level"],
            findings=["AI Intelligence currently unavailable."],
            reasoning=[alert["primary_reason"]],
            actions=[alert["recommended_action"]],
            data_state=alert["data_state"],
            sources=[f["source"] for f in alert["contributing_factors"]],
            limitations=["AI provider not reachable."],
            uncertainty=[]
        )
