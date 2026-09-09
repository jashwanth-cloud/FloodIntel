from typing import Dict, Any, List, Optional
from datetime import datetime

class IntelligenceSchema:
    @staticmethod
    def create_intelligence_response(
        summary: str,
        severity: str,
        findings: List[str],
        reasoning: List[str],
        actions: List[str],
        data_state: str,
        sources: List[str],
        limitations: List[str],
        uncertainty: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return {
            "status": "AVAILABLE",
            "summary": summary,
            "severity": severity,
            "key_findings": findings,
            "reasoning": reasoning,
            "recommended_actions": actions,
            "data_state": data_state,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "sources": sources,
            "limitations": limitations,
            "uncertainty": uncertainty or []
        }
