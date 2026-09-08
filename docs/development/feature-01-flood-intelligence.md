# Feature 01: Flood Intelligence Core

## Overview
This feature implements the foundational intelligence loop for FloodIntel:
1. User selects a location.
2. System retrieves current/historical rainfall.
3. Heavy-rainfall detection classifier runs.
4. Risk engine computes a risk score and level.
5. Frontend visualizes the risk intelligence on the map and dashboard.

## Architecture
- **Backend:** FastAPI (Python) service architecture.
- **Database:** PostgreSQL with PostGIS.
- **Frontend:** Next.js (React) with MapLibre GL JS for mapping.
- **ML:** Modular interfaces for detection and risk scoring.

## Implementation Decisions
- **Data State Transparency:** All data points must be tagged (REAL, HISTORICAL, DEMO, SIMULATED, UNAVAILABLE).
- **Service Abstraction:** Use providers for data (e.g., `RainfallProvider`) to allow switching from Demo/Historical to Real-time.
- **Geospatial:** PostGIS geometry types for location and spatial indexing.

## Data Flow
- **Request:** GET /api/v1/risk/{location_id}
- **Processing:** 
  1. Fetch location details from PostGIS.
  2. Fetch/Simulate rainfall observation.
  3. Run detection (Baseline model).
  4. Run Risk Engine.
  5. Return RiskAssessment (Score, Level, Factors, State).

## API Contracts (Simplified)
- `GET /api/v1/locations` -> `[Location]`
- `GET /api/v1/risk/{location_id}` -> `RiskAssessment`

## Testing Strategy
- **Backend:** Test service-level logic for risk calculation and detection.
- **Frontend:** Verify dashboard components against demo API data.
