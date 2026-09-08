# Feature 02: Real Historical Rainfall & ML Intelligence

## Status
- **IMD Historical Data:** UNAVAILABLE (Data not found in repository).
- **Fallback:** Currently using `DemoRainfallProvider`.

## Audit
- Searched repository for NetCDF/CSV files: None found.
- `data/` directory is empty.

## Implementation Plan
1. **Interface Definition:** Implement `IMDHistoricalRainfallProvider` raising `DataUnavailableError`.
2. **Provider Management:** Update `RainfallService` to support multiple providers and fallback logic.
3. **ML Pipeline Structure:** Define feature engineering, training, and inference interfaces in `ml/`.
4. **Integration:** Update API to reflect provenance and handle data states properly.
5. **Transparency:** Ensure frontend explicitly labels "DATA UNAVAILABLE" when IMD integration is attempted without data.

## ML Architecture (Planned)
- **Model:** Random Forest for Heavy Rainfall Detection (Classification).
- **Target:** Based on IMD threshold (requires actual data for definition).
- **Versioning:** Versioned artifacts in `models/`.
