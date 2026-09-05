import pandas as pd
import requests
from pathlib import Path

QUEUE_FILE = "download_queue.csv"
STAC_URL = "https://stac.dataspace.copernicus.eu/v1"
OUTPUT_DIR = Path("sentinel1_data")
TOKEN_FILE = Path("cdse_token.txt")

OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(QUEUE_FILE, low_memory=False)
scene_id = df.iloc[0]["scene_id"]

print("=" * 70)
print("SENTINEL-1 AUTHENTICATED VV + VH DOWNLOAD TEST")
print("=" * 70)

print("Scene:", scene_id)

# ------------------------------------------------------------
# Load authentication token
# ------------------------------------------------------------

if not TOKEN_FILE.exists():
    print("ERROR: cdse_token.txt not found.")
    print("Run: python .\\cdse_auth.py")
    raise SystemExit(1)

token = TOKEN_FILE.read_text().strip()

if not token:
    print("ERROR: Authentication token is empty.")
    raise SystemExit(1)

headers = {
    "Authorization": f"Bearer {token}"
}

print("Authentication token loaded.")

# ------------------------------------------------------------
# Get STAC item
# ------------------------------------------------------------

item_url = f"{STAC_URL}/collections/sentinel-1-grd/items/{scene_id}"

print()
print("Requesting STAC item...")

response = requests.get(
    item_url,
    headers=headers,
    timeout=60
)

print("STAC HTTP status:", response.status_code)

response.raise_for_status()

item = response.json()

assets = item.get("assets", {})

print("STAC item found.")

# ------------------------------------------------------------
# Find Product asset
# ------------------------------------------------------------

product_asset = assets.get("Product")

if not product_asset:
    print("ERROR: Product asset not found.")
    raise SystemExit(1)

product_url = product_asset["href"]

print()
print("Product URL found:")
print(product_url)

# ------------------------------------------------------------
# Extract Product ID
# ------------------------------------------------------------

prefix = "Products("
suffix = ")/$value"

if prefix not in product_url or suffix not in product_url:
    print("ERROR: Unexpected Product URL format.")
    raise SystemExit(1)

product_id = product_url.split(prefix, 1)[1].split(suffix, 1)[0]

print()
print("Product ID:", product_id)

# ------------------------------------------------------------
# Download complete product
# ------------------------------------------------------------

download_url = (
    f"https://download.dataspace.copernicus.eu/"
    f"odata/v1/Products({product_id})/$value"
)

output_file = OUTPUT_DIR / f"{scene_id}.zip"

print()
print("=" * 70)
print("DOWNLOADING AUTHENTICATED SENTINEL-1 PRODUCT")
print("=" * 70)

print("URL:", download_url)
print("Output:", output_file)

with requests.get(
    download_url,
    headers=headers,
    stream=True,
    timeout=180
) as r:

    print("Download HTTP status:", r.status_code)

    r.raise_for_status()

    total = 0

    with open(output_file, "wb") as f:

        for chunk in r.iter_content(chunk_size=1024 * 1024):

            if chunk:
                f.write(chunk)
                total += len(chunk)

print()
print("=" * 70)
print("DOWNLOAD SUCCESSFUL")
print("=" * 70)

print(
    f"Saved: {output_file}"
)

print(
    f"Size: {total / (1024 * 1024):.2f} MB"
)

print()
print("Next step: extract VV + VH from the downloaded product.")