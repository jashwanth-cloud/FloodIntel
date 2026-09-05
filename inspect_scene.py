import rasterio
from pathlib import Path

root = Path("sentinel1_data/extracted")

files = list(root.rglob("*.tiff"))

print("=" * 70)
print("SENTINEL-1 SCENE INSPECTION")
print("=" * 70)

for file in files:
    print("\nFILE:", file.name)

    with rasterio.open(file) as src:
        print("Width       :", src.width)
        print("Height      :", src.height)
        print("Bands       :", src.count)
        print("Data type   :", src.dtypes[0])
        print("CRS         :", src.crs)
        print("Resolution  :", src.res)
        print("Bounds      :", src.bounds)
        print("NoData      :", src.nodata)

        print("Min         :", src.read(1, masked=True).min())
        print("Max         :", src.read(1, masked=True).max())

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)