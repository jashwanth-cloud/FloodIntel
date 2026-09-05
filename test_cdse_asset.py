import requests

TOKEN_FILE = "cdse_token.txt"

SCENE_ID = "S1A_IW_GRDH_1SDV_20240820T003107_20240820T003132_055289_06BD9B_5392_COG"

STAC_URL = (
    f"https://stac.dataspace.copernicus.eu/v1/collections/"
    f"sentinel-1-grd/items/{SCENE_ID}"
)

token = open(TOKEN_FILE, encoding="utf-8").read().strip()

print("=" * 70)
print("CDSE SENTINEL-1 ASSET TEST")
print("=" * 70)

print("Getting asset URL from STAC...")

response = requests.get(STAC_URL, timeout=60)
response.raise_for_status()

item = response.json()

asset_url = item["assets"]["vv"]["alternate"]["https"]["href"]

print("Asset URL obtained.")
print("Testing authenticated access...")
print()

headers = {
    "Authorization": f"Bearer {token}",
    "Range": "bytes=0-1023",
}

r = requests.get(
    asset_url,
    headers=headers,
    timeout=60,
)

print("HTTP:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))
print("Content-Length:", r.headers.get("Content-Length"))
print("Content-Range:", r.headers.get("Content-Range"))
print("Bytes received:", len(r.content))

if r.status_code in (200, 206):
    print()
    print("=" * 70)
    print("SUCCESS — SENTINEL-1 IMAGE ACCESS WORKS")
    print("=" * 70)
else:
    print()
    print("SERVER RESPONSE:")
    print(r.text[:500])