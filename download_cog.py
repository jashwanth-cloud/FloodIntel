import requests
from pathlib import Path

TOKEN_FILE = Path("cdse_token.txt")
OUTPUT_DIR = Path("sentinel1_cog")

PRODUCT_ID = "f0070cbd-7af8-4d45-b253-e7e353263fe3"

SAFE_ID = (
    "S1A_IW_GRDH_1SDV_20240820T003107_20240820T003132_"
    "055289_06BD9B_5392_COG.SAFE"
)

BASE_URL = (
    "https://download.dataspace.copernicus.eu/odata/v1/"
    f"Products({PRODUCT_ID})/Nodes({SAFE_ID})/Nodes(measurement)/Nodes"
)

FILES = {
    "VV.tif": (
        "s1a-iw-grd-vv-20240820t003107-20240820t003132-"
        "055289-06bd9b-001-cog.tiff"
    ),
    "VH.tif": (
        "s1a-iw-grd-vh-20240820t003107-20240820t003132-"
        "055289-06bd9b-002-cog.tiff"
    ),
}


def download_file(filename, token):

    node_id = FILES[filename]

    url = f"{BASE_URL}({node_id})/$value"

    output = OUTPUT_DIR / filename

    print()
    print("=" * 70)
    print("DOWNLOADING:", filename)
    print("=" * 70)
    print("Output:", output)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    with requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=180
    ) as response:

        print("HTTP status:", response.status_code)

        response.raise_for_status()

        total = 0

        with open(output, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)

        print(
            f"Saved: {output}"
        )

        print(
            f"Size: {total / (1024 * 1024):.2f} MB"
        )


def main():

    if not TOKEN_FILE.exists():
        print("ERROR: cdse_token.txt not found.")
        raise SystemExit(1)

    token = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if not token:
        print("ERROR: Authentication token is empty.")
        raise SystemExit(1)

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    print("=" * 70)
    print("SENTINEL-1 COG DOWNLOADER")
    print("=" * 70)
    print("Scene: 5392_COG")
    print("Files: VV + VH")
    print("Destination:", OUTPUT_DIR)

    for filename in FILES:
        download_file(
            filename,
            token
        )

    print()
    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()