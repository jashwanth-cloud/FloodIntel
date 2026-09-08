from ..schemas.assessment_schema import RiskAssessment, RiskFactor
from ..ml.inference import HeavyRainfallInference

class RiskEngineService:
    def __init__(self):
        self.ml_detector = HeavyRainfallInference()

    def calculate_risk(self, location_id: int, rainfall_data: dict, lag_1: float = 0.0, rolling_mean_3: float = 0.0) -> RiskAssessment:
        amount = rainfall_data.get("amount", 0)
        
        # Get ML prediction
        ml_result = self.ml_detector.predict(amount, lag_1, rolling_mean_3)
        
        # Risk logic using ML signal
        if ml_result["heavy_rainfall_detected"]:
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
                    factor="Heavy Rainfall Detection (ML)",
                    impact=level,
                    value=float(ml_result["heavy_rainfall_detected"]),
                    unit="bool",
                    description=f"ML model detection: {ml_result['heavy_rainfall_detected']}"
                ),
                RiskFactor(
                    factor="Rainfall Intensity",
                    impact=level,
                    value=amount,
                    unit="mm",
                    description=f"Observed rainfall of {amount} mm."
                )
            ],
            model_version=ml_result["model_version"],
            data_state=rainfall_data.get("data_state", "HISTORICAL")
        )
