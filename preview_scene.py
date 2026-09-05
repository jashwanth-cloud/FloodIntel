import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

root = Path("sentinel1_data/extracted")

files = {
    "VV": next(root.rglob("*-vv-*.tiff")),
    "VH": next(root.rglob("*-vh-*.tiff")),
}

for name, path in files.items():

    print(f"Reading {name}...")

    with rasterio.open(path) as src:
        # Read a reduced version instead of the entire 500+ MB raster
        scale = 20

        data = src.read(
            1,
            out_shape=(
                1,
                src.height // scale,
                src.width // scale
            )
        ).astype(np.float32)

    data[data <= 0] = np.nan

    # Log transform makes radar intensity easier to visualize
    data = 10 * np.log10(data)

    low, high = np.nanpercentile(data, [2, 98])
    data = np.clip(data, low, high)

    plt.figure(figsize=(12, 8))
    plt.imshow(data, cmap="gray")
    plt.title(f"Sentinel-1 {name}")
    plt.axis("off")
    plt.tight_layout()

    output = root / f"{name}_preview.png"
    plt.savefig(output, dpi=150)
    plt.close()

    print("Saved:", output)

print("\nPreview generation complete.")