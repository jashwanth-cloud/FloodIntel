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
        if ml_result["heavy_rainfall_predicted"]:
            level = "SEVERE"
            score = 80 + int(ml_result["probability"] * 20)
        elif amount > 50:
            level = "HIGH"
            score = 70
        elif amount > 20:
            level = "MODERATE"
            score = 45
        else:
            level = "LOW"
            score = 15
            
        # Normalize timestamp to string
        ts = rainfall_data.get("timestamp")
        if isinstance(ts, (datetime,)):
            ts = ts.isoformat()
        elif ts is None:
            ts = datetime.now(timezone.utc).isoformat()
            
        return RiskAssessment(
            location_id=location_id,
            timestamp=ts,
            risk_score=min(score, 100),
            risk_level=level,
            factors=[
                RiskFactor(
                    factor="Next-Day Heavy Rainfall Prediction (ML)",
                    impact=level,
                    value=float(ml_result["probability"]),
                    unit="prob",
                    description=f"ML model prediction probability for tomorrow: {ml_result['probability']:.2f} (Threshold: {ml_result['threshold']:.2f})"
                ),
                RiskFactor(
                    factor="Rainfall Intensity",
                    impact=level,
                    value=amount,
                    unit="mm",
                    description=f"Observed rainfall today: {amount} mm."
                )
            ],
            model_version=ml_result["model_version"],
            data_state=rainfall_data.get("data_state", "HISTORICAL")
        )
