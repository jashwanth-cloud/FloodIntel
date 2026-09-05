import pandas as pd
import requests

QUEUE_FILE = "download_queue.csv"

STAC_URL = "https://stac.dataspace.copernicus.eu/v1"

df = pd.read_csv(QUEUE_FILE, low_memory=False)

scene_id = df.iloc[0]["scene_id"]

print("=" * 70)
print("SENTINEL-1 STAC SCENE TEST")
print("=" * 70)

print("Scene:", scene_id)

url = f"{STAC_URL}/collections/sentinel-1-grd/items/{scene_id}"

print()
print("Requesting:")
print(url)

response = requests.get(url, timeout=60)

print()
print("HTTP status:", response.status_code)

if response.status_code != 200:
    print()
    print("SERVER RESPONSE:")
    print(response.text[:2000])
    raise SystemExit(1)

item = response.json()

print()
print("STAC ITEM FOUND")
print("=" * 70)

print("ID:", item.get("id"))
print("Collection:", item.get("collection"))

print()
print("Available assets:")

for name, asset in item.get("assets", {}).items():
    print()
    print("Asset:", name)
    print("Type:", asset.get("type"))
    print("Title:", asset.get("title"))
    print("Href:", asset.get("href"))

print()
print("=" * 70)
print("STAC TEST SUCCESSFUL")
print("=" * 70)