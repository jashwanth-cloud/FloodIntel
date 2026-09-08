# IMD Rainfall Dataset (2018-2025)

## Source
Indian Meteorological Department (IMD) gridded rainfall data.

## Files
- Files: RF25_indYYYY_rfp25.nc (2018-2025)
- Local Path: `data/raw/rainfall/`

## Properties
- Format: NetCDF
- State: HISTORICAL

## Limitations
- Resolution: 0.25 deg x 0.25 deg
- Ingestion: NetCDF via xarray

## Ingestion Method
- Use `xarray` to open and process NetCDF files efficiently without loading entire dataset into memory.
