import pandas as pd
import requests
from pathlib import Path
import time

# ============================================================
# CDSE SENTINEL-1 FLOOD ASSET DOWNLOADER
# ============================================================

INPUT_FILE = Path("flood_imagery_assets.csv")
TOKEN_FILE = Path("cdse_token.txt")
DOWNLOAD_DIR = Path("flood_downloads")

DOWNLOAD_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 1024 * 1024  # 1 MB

print("=" * 70)
print("CDSE SENTINEL-1 FLOOD ASSET DOWNLOADER")
print("=" * 70)

# ------------------------------------------------------------
# Load token
# ------------------------------------------------------------

if not TOKEN_FILE.exists():
    raise FileNotFoundError("cdse_token.txt not found.")

token = TOKEN_FILE.read_text().strip()

if not token:
    raise ValueError("cdse_token.txt is empty.")

print("CDSE token loaded.")
print("Token length:", len(token))

# ------------------------------------------------------------
# Load selected scenes
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Selected scenes:", len(df))
print()

# ------------------------------------------------------------
# Get authenticated HTTPS asset URL from STAC
# ------------------------------------------------------------

def get_https_asset_url(scene_id, polarization):

    print(f"Getting {polarization.upper()} asset URL from STAC...")

    stac_url = (
        "https://stac.dataspace.copernicus.eu/v1/"
        f"collections/sentinel-1-grd/items/{scene_id}"
    )

    response = requests.get(
        stac_url,
        timeout=30
    )

    response.raise_for_status()

    item = response.json()

    asset = item["assets"][polarization]

    https_url = asset["alternate"]["https"]["href"]

    return https_url


# ------------------------------------------------------------
# Download function
# ------------------------------------------------------------

def download_file(url, output_path, label):

    headers = {
        "Authorization": "Bearer " + token
    }

    existing_size = 0

    if output_path.exists():
        existing_size = output_path.stat().st_size

    print("-" * 70)
    print(label)
    print("Output:", output_path)

    if existing_size > 0:

        print(
            "Existing partial file:",
            round(existing_size / (1024 * 1024), 2),
            "MB"
        )

        headers["Range"] = f"bytes={existing_size}-"

    print("Connecting to CDSE...")

    response = requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=(30, 120)
    )

    print("HTTP:", response.status_code)

    if response.status_code not in (200, 206):

        print("ERROR:")
        print(response.text[:500])

        return False

    content_length = response.headers.get("Content-Length")

    if content_length:

        content_length = int(content_length)

        if response.status_code == 206:
            total_size = existing_size + content_length
        else:
            total_size = content_length

    else:

        total_size = None

    if total_size:

        print(
            "Total size:",
            round(total_size / (1024 * 1024), 2),
            "MB"
        )

    mode = "ab" if response.status_code == 206 else "wb"

    downloaded = existing_size if mode == "ab" else 0

    start_time = time.time()

    with open(output_path, mode) as f:

        for chunk in response.iter_content(CHUNK_SIZE):

            if not chunk:
                continue

            f.write(chunk)

            downloaded += len(chunk)

            elapsed = time.time() - start_time

            if elapsed > 0:
                speed = (
                    downloaded
                    / elapsed
                    / (1024 * 1024)
                )
            else:
                speed = 0

            if total_size:

                percent = (
                    downloaded
                    / total_size
                    * 100
                )

                print(
                    f"\rProgress: {percent:6.2f}% | "
                    f"{downloaded / (1024*1024):8.1f} MB / "
                    f"{total_size / (1024*1024):8.1f} MB | "
                    f"{speed:6.2f} MB/s",
                    end=""
                )

            else:

                print(
                    f"\rDownloaded: "
                    f"{downloaded / (1024*1024):.1f} MB | "
                    f"{speed:.2f} MB/s",
                    end=""
                )

    print()

    final_size = output_path.stat().st_size

    print(
        "Saved:",
        output_path,
        f"({final_size / (1024*1024):.2f} MB)"
    )

    return True


# ============================================================
# DOWNLOAD SELECTED ASSETS
# ============================================================

for _, row in df.iterrows():

    role = row["role"]
    scene_id = row["scene_id"]

    print()
    print("=" * 70)
    print("SCENE:", role.upper())
    print("ID:", scene_id)
    print("DATE:", row["date"])
    print("=" * 70)

    # --------------------------------------------------------
    # VV
    # --------------------------------------------------------

    vv_file = DOWNLOAD_DIR / f"{role}_vv.tiff"

    print()
    print("Downloading VV...")

    try:

        vv_url = get_https_asset_url(
            scene_id,
            "vv"
        )

        print("HTTPS asset URL obtained.")

        success = download_file(
            vv_url,
            vv_file,
            f"{role.upper()} VV"
        )

    except Exception as e:

        print("VV ERROR:", e)
        success = False

    if not success:

        print("VV download failed.")
        continue

    # --------------------------------------------------------
    # VH
    # --------------------------------------------------------

    vh_file = DOWNLOAD_DIR / f"{role}_vh.tiff"

    print()
    print("Downloading VH...")

    try:

        vh_url = get_https_asset_url(
            scene_id,
            "vh"
        )

        print("HTTPS asset URL obtained.")

        success = download_file(
            vh_url,
            vh_file,
            f"{role.upper()} VH"
        )

    except Exception as e:

        print("VH ERROR:", e)
        success = False

    if not success:

        print("VH download failed.")
        continue


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("DOWNLOAD COMPLETE")
print("=" * 70)

print()
print("Downloaded files:")

for file in sorted(DOWNLOAD_DIR.glob("*.tiff")):

    size_mb = (
        file.stat().st_size
        / (1024 * 1024)
    )

    print(
        f"  {file.name:20s} "
        f"{size_mb:10.2f} MB"
    )

print()
print("Files are stored in:")
print(DOWNLOAD_DIR.resolve())