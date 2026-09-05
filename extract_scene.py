import zipfile
from pathlib import Path

ZIP_FILE = Path("sentinel1_data/S1A_IW_GRDH_1SDV_20180529T003359_20180529T003424_022112_026403_96EE_COG.zip")
OUTPUT_DIR = Path("sentinel1_data/extracted")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("SENTINEL-1 VV + VH EXTRACTION")
print("=" * 70)

with zipfile.ZipFile(ZIP_FILE, "r") as z:

    files = z.namelist()

    vv = [f for f in files if "/measurement/" in f and "-vv-" in f and f.endswith(".tiff")]
    vh = [f for f in files if "/measurement/" in f and "-vh-" in f and f.endswith(".tiff")]

    print("\nVV file:")
    print(vv[0] if vv else "NOT FOUND")

    print("\nVH file:")
    print(vh[0] if vh else "NOT FOUND")

    if not vv or not vh:
        raise RuntimeError("VV or VH image not found")

    print("\nExtracting VV...")
    z.extract(vv[0], OUTPUT_DIR)

    print("Extracting VH...")
    z.extract(vh[0], OUTPUT_DIR)

print("\n" + "=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)

for p in OUTPUT_DIR.rglob("*.tiff"):
    print(f"{p} | {p.stat().st_size / (1024 * 1024):.2f} MB")