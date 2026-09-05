import os
import sys
import json
import requests
from pathlib import Path


# ================================================================
# SIH 26071 — COPERNICUS DEM GLO-30 TEST DOWNLOADER
# ================================================================
#
# Uses:
#   Copernicus Data Space Ecosystem
#   OData Catalogue
#   Official CDSE user authentication
#
# IMPORTANT:
#   Do NOT put username/password directly in this file.
#
# PowerShell:
#   $env:CDSE_USERNAME="your_cdse_username"
#   $env:CDSE_PASSWORD="your_cdse_password"
#
# ================================================================


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "dem"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------
# CDSE endpoints
# ----------------------------------------------------------------

AUTH_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

CATALOGUE_URL = (
    "https://catalogue.dataspace.copernicus.eu/"
    "odata/v1/Products"
)

DOWNLOAD_URL = (
    "https://download.dataspace.copernicus.eu/"
    "odata/v1/Products"
)


# ----------------------------------------------------------------
# DEM information
# ----------------------------------------------------------------

COLLECTION_NAME = "CCM"

DATASET_NAME = "COP-DEM_GLO-30-DGED"

PRODUCT_TYPE = "SAR_DGE_30_A4AD"


# Test point inside India
TEST_LON = 80.0
TEST_LAT = 16.0


# ----------------------------------------------------------------
# Utility
# ----------------------------------------------------------------

def print_header(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def fail(message):
    print()
    print("=" * 72)
    print("❌ DEM TEST FAILED")
    print("=" * 72)
    print()
    print(message)
    print()
    sys.exit(1)


# ----------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------

def get_access_token():
    print()
    print("-" * 72)
    print("AUTHENTICATION")
    print("-" * 72)

    username = os.getenv("CDSE_USERNAME")
    password = os.getenv("CDSE_PASSWORD")

    if not username:
        fail(
            "CDSE_USERNAME is not set.\n\n"
            "Run:\n"
            '$env:CDSE_USERNAME="your_username"'
        )

    if not password:
        fail(
            "CDSE_PASSWORD is not set.\n\n"
            "Run:\n"
            '$env:CDSE_PASSWORD="your_password"'
        )

    print("Using CDSE user authentication...")
    print("Username: SET")
    print("Password: SET")

    data = {
        "client_id": "cdse-public",
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(
            AUTH_URL,
            data=data,
            timeout=60,
        )
    except requests.RequestException as exc:
        fail(f"Authentication request failed:\n{exc}")

    if response.status_code != 200:
        print()
        print("HTTP:", response.status_code)
        print(response.text)
        fail("CDSE authentication failed.")

    try:
        payload = response.json()
    except ValueError:
        fail("CDSE returned a non-JSON authentication response.")

    access_token = payload.get("access_token")

    if not access_token:
        print(json.dumps(payload, indent=2))
        fail("No access_token was returned by CDSE.")

    print("✓ CDSE authentication successful")

    return access_token


# ----------------------------------------------------------------
# Search DEM catalogue
# ----------------------------------------------------------------

def search_dem_product():
    print_header("SEARCHING CDSE CATALOGUE")

    print()
    print("Collection:")
    print(f"  {COLLECTION_NAME}")

    print()
    print("Dataset:")
    print(f"  {DATASET_NAME}")

    print()
    print("Product type:")
    print(f"  {PRODUCT_TYPE}")

    # IMPORTANT:
    #
    # Do NOT use startswith() here.
    #
    # CDSE currently rejects that function in some attribute
    # expressions.
    #
    # We search by Collection + productType first and then inspect
    # returned products locally.
    #
    filter_expression = (
        "Collection/Name eq 'CCM' "
        "and "
        "Attributes/OData.CSC.StringAttribute/any("
        "att:att/Name eq 'productType' "
        "and "
        "att/OData.CSC.StringAttribute/Value eq "
        "'SAR_DGE_30_A4AD'"
        ")"
    )

    params = {
        "$filter": filter_expression,
        "$top": "100",
        "$select": (
            "Id,"
            "Name,"
            "S3Path,"
            "GeoFootprint,"
            "ContentDate,"
            "ContentLength"
        ),
    }

    print()
    print("Sending OData request...")

    try:
        response = requests.get(
            CATALOGUE_URL,
            params=params,
            timeout=120,
        )
    except requests.RequestException as exc:
        fail(f"Catalogue request failed:\n{exc}")

    print()
    print("HTTP:", response.status_code)

    if response.status_code != 200:
        print()
        print(response.text)
        fail("CDSE catalogue search failed.")

    try:
        payload = response.json()
    except ValueError:
        fail("CDSE returned invalid JSON.")

    products = payload.get("value", [])

    print()
    print("✓ Products returned:", len(products))

    if not products:
        fail(
            "No DEM products were returned.\n\n"
            "The catalogue query did not find any GLO-30 products."
        )

    # ------------------------------------------------------------
    # Find a product whose footprint contains / surrounds
    # test location.
    #
    # We first try a simple bounding-box test.
    # ------------------------------------------------------------

    matching_product = None

    for product in products:

        footprint = product.get("GeoFootprint")

        if not footprint:
            continue

        try:
            coordinates = footprint["coordinates"]

            # Polygon:
            # coordinates[0] = outer ring
            #
            # MultiPolygon:
            # coordinates[0][0] = outer ring

            geometry_type = footprint.get("type")

            points = []

            if geometry_type == "Polygon":
                points = coordinates[0]

            elif geometry_type == "MultiPolygon":
                points = coordinates[0][0]

            else:
                continue

            lons = [float(point[0]) for point in points]
            lats = [float(point[1]) for point in points]

            min_lon = min(lons)
            max_lon = max(lons)
            min_lat = min(lats)
            max_lat = max(lats)

            if (
                min_lon <= TEST_LON <= max_lon
                and
                min_lat <= TEST_LAT <= max_lat
            ):
                matching_product = product
                break

        except Exception:
            continue

    # If no matching footprint was found, use first product.
    # This is still useful for testing authentication/download.
    if matching_product is None:
        print()
        print(
            "⚠ No returned footprint matched the test coordinate."
        )
        print(
            "Using the first catalogue product for download test."
        )

        matching_product = products[0]

    return matching_product


# ----------------------------------------------------------------
# Print product information
# ----------------------------------------------------------------

def show_product(product):
    print()
    print("-" * 72)
    print("SELECTED DEM PRODUCT")
    print("-" * 72)

    print()
    print("ID:")
    print(product.get("Id"))

    print()
    print("Name:")
    print(product.get("Name"))

    print()
    print("S3Path:")
    print(product.get("S3Path"))

    print()
    print("ContentLength:")
    print(product.get("ContentLength"))

    print()
    print("ContentDate:")
    print(json.dumps(product.get("ContentDate"), indent=2))

    print()
    print("GeoFootprint:")
    print(json.dumps(product.get("GeoFootprint"), indent=2))


# ----------------------------------------------------------------
# Download product
# ----------------------------------------------------------------

def download_product(access_token, product):
    print_header("DOWNLOADING DEM PRODUCT")

    product_id = product.get("Id")
    product_name = product.get("Name")

    if not product_id:
        fail("Selected product has no ID.")

    if not product_name:
        product_name = f"dem_{product_id}.zip"

    # DEM products are delivered as downloadable products.
    output_file = OUTPUT_DIR / f"{product_name}.zip"

    url = f"{DOWNLOAD_URL}({product_id})/$value"

    print()
    print("Product:")
    print(product_name)

    print()
    print("Product ID:")
    print(product_id)

    print()
    print("Download URL:")
    print(url)

    print()
    print("Output:")
    print(output_file)

    print()
    print("Starting download...")
    print()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "SIH26071-Copernicus-India-Flood/1.0",
    }

    try:
        with requests.get(
            url,
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=120,
        ) as response:

            print("HTTP:", response.status_code)

            if response.status_code != 200:
                print()
                print("Download response:")
                print(response.text[:5000])

                fail(
                    "DEM download failed.\n\n"
                    "If the response contains 'Token audience not allowed', "
                    "the authentication token is from the wrong CDSE flow."
                )

            total_bytes = 0

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:
                try:
                    total_size = int(content_length)
                except ValueError:
                    total_size = None
            else:
                total_size = None

            with open(output_file, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if not chunk:
                        continue

                    file.write(chunk)

                    total_bytes += len(chunk)

                    downloaded_mb = (
                        total_bytes / (1024 * 1024)
                    )

                    if total_size:
                        total_mb = (
                            total_size / (1024 * 1024)
                        )

                        percent = (
                            total_bytes / total_size
                        ) * 100

                        print(
                            f"\rDownloaded: "
                            f"{downloaded_mb:.2f} MB / "
                            f"{total_mb:.2f} MB "
                            f"({percent:.1f}%)",
                            end="",
                            flush=True,
                        )

                    else:
                        print(
                            f"\rDownloaded: "
                            f"{downloaded_mb:.2f} MB",
                            end="",
                            flush=True,
                        )

            print()

    except requests.RequestException as exc:
        fail(f"Download request failed:\n{exc}")

    if not output_file.exists():
        fail("Download finished but output file does not exist.")

    file_size = output_file.stat().st_size

    if file_size == 0:
        output_file.unlink(missing_ok=True)
        fail("Downloaded file is empty.")

    print()
    print("-" * 72)
    print("✓ DOWNLOAD COMPLETE")
    print("-" * 72)

    print()
    print("File:")
    print(output_file)

    print()
    print(
        f"Size: {file_size / (1024 * 1024):.2f} MB"
    )

    return output_file


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------

def main():

    print_header(
        "SIH 26071 — COPERNICUS DEM GLO-30\n"
        "CDSE OData TEST DOWNLOADER"
    )

    print()
    print("Project:")
    print(PROJECT_ROOT)

    print()
    print("Output:")
    print(OUTPUT_DIR)

    print()
    print("Collection:")
    print(COLLECTION_NAME)

    print()
    print("Dataset:")
    print(DATASET_NAME)

    print()
    print("Product Type:")
    print(PRODUCT_TYPE)

    print()
    print("Test location:")
    print(f"  Longitude: {TEST_LON}")
    print(f"  Latitude : {TEST_LAT}")

    # Authentication
    access_token = get_access_token()

    # Catalogue
    product = search_dem_product()

    # Display
    show_product(product)

    print()
    print_header("✓ DEM CATALOGUE ACCESS CONFIRMED")

    print()
    print(
        "A valid Copernicus DEM GLO-30 product was found."
    )

    print()
    print(
        "The program will now download ONE product only."
    )

    # Download
    output_file = download_product(
        access_token,
        product,
    )

    print()
    print("=" * 72)
    print("🎉 DEM TEST SUCCESSFUL")
    print("=" * 72)

    print()
    print("Downloaded file:")
    print(output_file)

    print()
    print(
        "Next step: after this test succeeds, "
        "we can build the India-wide DEM collector."
    )

    print()


if __name__ == "__main__":
    main()