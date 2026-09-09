# Feature 06: Satellite Flood Detection

## Overview
This feature implements a historical satellite-derived flood observation layer based on Copernicus GFM (Global Flood Monitoring) data. It provides an API and frontend visualization to display historical flood extents.

## Data Source
- **Product:** Copernicus GFM-derived Flood Raster
- **Source File:** `data/processed/feature04/validated_flood_label.tif`
- **Event Date:** 2024-09-01
- **Data State:** HISTORICAL (NOT live, NOT predicted)

## Technical Details
- **CRS:** (To be determined/verified from file metadata)
- **Spatial Extent:** Derived from raster bounds
- **Resolution:** Derived from raster metadata

## Leakage Considerations
- The GFM-derived flood extent is a ground-truth reference observation (historical).
- It is NOT an early-warning predictor.
- Feature 04 predictive training remains leakage-safe.
- This layer MUST be presented as HISTORICAL in the UI to prevent confusion with real-time predictions.

## Backend API
- `GET /api/v1/satellite/flood/{location_id}`
- Returns metadata and flood area calculation (if applicable).

## Frontend Integration
- Integrates into MapLibre as a distinct "Historical Observation" layer.

## Limitations
- Single-event POC implementation (2024-09-01).
- Limited to the spatial extent of the provided raster.
