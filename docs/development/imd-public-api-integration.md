# IMD Public API Integration

## Official Endpoint
`https://api.imd.gov.in/public/current_wx`

## Configuration
- `IMD_API_BASE_URL`: Base URL for IMD API.
- `IMD_API_KEY`: API Key (if required).
- `IMD_API_ENABLED`: Boolean (set to `true` to enable live fetching).
- `IMD_API_TIMEOUT`: Timeout in seconds.
- `IMD_CACHE_TTL`: Cache duration in seconds.

## Normalization
Internal schema:
- `source`: "IMD"
- `data_state`: "LIVE" | "DEMO" | "UNAVAILABLE" | "ERROR"
- `temperature`: float
- `weather_condition`: str
- `fetched_at`: float (timestamp)

## Fallback Behavior
- **Enabled + Success:** `LIVE`
- **Disabled/Failure + Demo Mode Enabled:** `DEMO`
- **Failure:** `ERROR`

## Caching
- In-memory bounded TTL cache per location (lat/lon).

## Attribution
- All responses include source metadata clearly identifying "IMD" as the originator.
