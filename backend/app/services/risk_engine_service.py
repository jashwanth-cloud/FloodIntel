from ..schemas.assessment_schema import RiskAssessment, RiskFactor

class RiskEngineService:
    def calculate_risk(self, location_id: int, rainfall_data: dict) -> RiskAssessment:
        amount = rainfall_data.get("amount", 0)
        
        # Simple risk logic for demonstration
        if amount > 80:
            level = "SEVERE"
            score = 85
        elif amount > 50:
            level = "HIGH"
            score = 70
        elif amount > 20:
            level = "MODERATE"
            score = 45
        else:
            level = "LOW"
            score = 15
            
        return RiskAssessment(
            location_id=location_id,
            timestamp=rainfall_data.get("timestamp"),
            risk_score=score,
            risk_level=level,
            factors=[
                RiskFactor(
                    factor="Rainfall Intensity",
                    impact=level,
                    value=amount,
                    unit="mm",
                    description=f"Observed rainfall of {amount} mm is the primary driver."
                )
            ],
            model_version="baseline-v1.0",
            data_state=rainfall_data.get("data_state", "DEMO")
        )
