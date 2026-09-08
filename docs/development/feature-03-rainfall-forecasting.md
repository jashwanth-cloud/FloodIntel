# Feature 03: Rainfall Forecasting

## Overview
This feature implements a next-day rainfall forecasting model (regression).
- Target: `RAINFALL(T+1)`
- Features: `RAINFALL(T)`, `lag_1(T-1)`, `rolling_mean_3(T)`
- Baseline: Persistence (Forecast(T+1) = Rainfall(T))

## Implementation Plan
1. **Dataset Preparation:** Refactor `trainer.py` to support regression target.
2. **Persistence Baseline:** Calculate MAE/RMSE for `Forecast = Rainfall(T)`.
3. **ML Training:** Train `RandomForestRegressor` on 2018–2022.
4. **Versioning:** Artifact in `models/rainfall_forecasting/random_forest/v1/`.
5. **Inference:** Implement `Forecaster` inference service.
6. **API:** Add `GET /api/v1/forecast/rainfall/{location_id}`.
7. **UI:** Visualization of forecast.

## Leakage Audit
- Features use only information available at `T`.
- Target uses `T+1` (next day).
- Strict chronological split (2018-2022/2023-2024/2025) prevents leakage.
