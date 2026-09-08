# Feature 02B: Real Heavy-Rainfall ML Model Implementation

## Dataset Audit
- **Files:** 8 files (2018-2025), NetCDF.
- **Resolution:** 0.25 deg x 0.25 deg.
- **Variable:** RAINFALL (mm).
- **Dimensions:** TIME, LATITUDE, LONGITUDE.

## Training Pipeline Plan
1. **Target:** `heavy_rainfall` if `RAINFALL >= 50mm` (1-day). Rationale: Typical threshold for heavy rainfall event classification.
2. **Features:** `RAINFALL` (current day), `RAINFALL_1d_lag` (previous day), `RAINFALL_3d_rolling_mean`.
3. **Split:** 
   - Train: 2018-2022
   - Validation: 2023
   - Test: 2024-2025
4. **Model:** Random Forest Classifier.
5. **Class Imbalance:** Use `class_weight='balanced'`.

## ML Directory Structure
- `backend/app/ml/trainer.py`: Training script.
- `backend/app/ml/inference.py`: Inference service.
- `models/heavy_rainfall/random_forest/v1/`: Artifacts and metadata.
