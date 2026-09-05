# Ward Boundary Data — Missing Dependency

## Status: ⛔ MISSING

No ward, district, or municipality boundary files were found in this project.

## What Was Searched

The following locations were checked and found empty:

- `data/raw/admin/`
- `data/raw/india_ward_boundaries.*`
- `metadata/india_ward_boundaries.*`
- All files in the project matching keywords: ward, admin, district, municipality, taluk

## Only Admin-Related File Found

`data/raw/hydrology/water_bodies/reports/surface_waterbodies_state_index.json`

This is NOT an administrative boundary file. It is a state-level index of
surface waterbody processing reports, not geometry boundaries.

## Impact on Phase 3

The following planned features CANNOT be computed without ward boundaries:

| Feature | Status |
|---------|--------|
| ward_id | ❌ Not possible |
| district_id | ❌ Not possible |
| state_id | ❌ Not possible |
| Ward-level rainfall aggregation | ❌ Not possible |
| Ward-level DEM aggregation | ❌ Not possible |
| Ward-level waterbody features | ❌ Not possible |
| Ward-level flood risk score | ❌ Not possible |

## What CAN Be Done

Environmental features (rainfall, DEM, waterbody proximity) CAN be computed
at the **grid-cell level** (lat/lon point) and at the **flood AOI raster level**.
These can later be aggregated to ward level once boundaries are obtained.

## Recommended Action for Phase 4

Obtain administrative boundary data from one of the following sources:

1. **GADM** (Global Administrative Areas):
   - URL: https://gadm.org/download_country.html
   - Select India (IND), Level 3 (district) or Level 4 (sub-district/taluk)
   - Format: GeoJSON or Shapefile

2. **Bhuvan / Survey of India**:
   - URL: https://bhuvan.nrsc.gov.in/
   - Open government geospatial portal for India

3. **Open Government Data Platform India**:
   - URL: https://data.gov.in/
   - Search for "ward boundaries" or "municipal boundaries"

4. **Municipal corporation websites** (if specific city):
   - e.g., VMRDA (Vijayawada Metropolitan Region Development Authority)
   - The AOI appears to be near Vijayawada, Andhra Pradesh

## File Placement

Once obtained, place the file at:
```
data/raw/admin/india_ward_boundaries.geojson
```
Then re-run:
```bash
python scripts/data_processing/admin_pipeline.py
```

## Current Fallback

The feature dataset uses grid-cell level lat/lon as geographic identifiers
instead of ward IDs. When ward boundaries become available, a spatial join
can be performed to assign ward_id, district_id, etc. to each grid cell.
