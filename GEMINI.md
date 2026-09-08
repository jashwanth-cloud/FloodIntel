# FloodIntel - Project Engineering Contract

## Core Mandates
- **Build Actual Working Software:** Do not build placeholders or mocks. Implement real features, connecting frontend, backend, database, and ML pipelines.
- **No Fabrication:** Never fabricate data, model metrics (accuracy, precision, F1, etc.), or predictions. If a feature or data is unavailable, clearly label it as 'UNAVAILABLE' or 'DEMO ONLY'.
- **Transparency:** Clearly distinguish between LIVE, HISTORICAL, DEMO, and SIMULATED data in the UI.
- **Modularity:** Keep ML pipelines, frontend, backend, and data ingestion logically separate and modular.
- **Continuity:** Do not get stuck on one feature. If a feature is blocked, create the interface, handle the failure gracefully, and continue with other workstreams.
- **Testing:** Test changes incrementally. Build tests for backend APIs, database interactions, ML preprocessing, and critical frontend user flows.
- **Quality:** Maintain production-quality architecture. Use type safety, environment configuration, error handling, and structured logging.
- **Maintainability:** Never replace working functionality with placeholders. Preserve working features.
- **Runnability:** The system must always be runnable, testable, and demonstrable.

## Project Structure
- `frontend/`: React/Next.js frontend.
- `backend/`: Python/FastAPI backend.
- `ml/`: AI/ML pipeline implementations.
- `data/`: Data ingestion, processing, and storage.
- `database/`: Database schema, migrations, and PostGIS configuration.
- `docs/`: Project documentation and architecture decisions.
- `infrastructure/`: Infrastructure configurations.
- `docker/`: Docker containerization files.

## Technical Standards
- **AI-First:** Integrate AI/ML across all modules (rainfall, flooding, alerts, reports).
- **GIS-Centric:** Use appropriate geospatial technologies (PostGIS, MapLibre/Leaflet).
- **Responsive:** Build a mobile-responsive interface (prioritize mobile-first where applicable).
- **Environment:** Use `.env` files for secrets (never commit these).
- **Communication:** Frontend/Backend must communicate via REST APIs.

## Definition of Done
- Implementation + Integration + Verification + Testing + Documentation.
- Features are only complete when verified against the PRD.
