import requests
import pandas as pd
import os
import time

STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

INDIA_BBOX = [
    68.0,
    6.0,
    97.5,
    37.5
]

START_YEAR = 2018
END_YEAR = 2025

OUTPUT_FILE = "sentinel1_india_2018_2025_full.csv"

PAGE_LIMIT = 100


def search_page(payload):

    response = requests.post(
        STAC_URL,
        json=payload,
        timeout=180
    )

    if response.status_code != 200:
        print("HTTP ERROR:", response.status_code)
        print(response.text[:1000])
        response.raise_for_status()

    return response.json()


def collect_month(year, month):

    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    start_date = (
        f"{year}-{month:02d}-01T00:00:00Z"
    )

    end_date = (
        f"{next_year}-{next_month:02d}-01T00:00:00Z"
    )

    payload = {

        "collections": [
            "sentinel-1-grd"
        ],

        "bbox": INDIA_BBOX,

        "datetime":
            f"{start_date}/{end_date}",

        "query": {

            "product:type": {
                "eq": "IW_GRDH_1S"
            },

            "sar:polarizations": {
                "eq": ["VV", "VH"]
            }
        },

        "limit": PAGE_LIMIT
    }

    results = []

    page = 1

    while True:

        data = search_page(payload)

        features = data.get(
            "features",
            []
        )

        results.extend(features)

        print(
            f"    Page {page}: "
            f"{len(features)} products | "
            f"Month total: {len(results)}"
        )

        next_link = None

        for link in data.get("links", []):

            if link.get("rel") == "next":

                next_link = link

                break

        if not next_link:
            break

        next_body = next_link.get("body")

        if not next_body:
            print(
                "    Next page has no POST body."
            )
            break

        payload = next_body

        page += 1

        time.sleep(0.2)

    rows = []

    for item in results:

        properties = item.get(
            "properties",
            {}
        )

        rows.append({

            "scene_id":
                item.get("id"),

            "date":
                properties.get(
                    "datetime"
                ),

            "platform":
                properties.get(
                    "platform"
                ),

            "product_type":
                properties.get(
                    "product:type"
                ),

            "instrument_mode":
                properties.get(
                    "sar:instrument_mode"
                ),

            "polarizations":
                properties.get(
                    "sar:polarizations"
                ),

            "orbit_state":
                properties.get(
                    "sat:orbit_state"
                ),

            "bbox":
                item.get("bbox")
        })

    return rows


def save_results(rows):

    if not rows:
        return

    new_df = pd.DataFrame(rows)

    if os.path.exists(OUTPUT_FILE):

        old_df = pd.read_csv(
            OUTPUT_FILE
        )

        df = pd.concat(
            [old_df, new_df],
            ignore_index=True
        )

    else:

        df = new_df

    df = df.drop_duplicates(
        subset=["scene_id"]
    )

    df = df.sort_values(
        "date"
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"    TOTAL UNIQUE SCENES: {len(df)}"
    )


def already_collected(year, month):

    if not os.path.exists(OUTPUT_FILE):
        return False

    try:

        df = pd.read_csv(
            OUTPUT_FILE
        )

        if "date" not in df.columns:
            return False

        dates = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        return (
            (dates.dt.year == year)
            &
            (dates.dt.month == month)
        ).any()

    except Exception:

        return False


def main():

    print()
    print("=" * 70)
    print("INDIA SENTINEL-1 FULL COLLECTOR")
    print("=" * 70)

    print(
        "Collection : Sentinel-1 GRD"
    )

    print(
        "Mode       : IW"
    )

    print(
        "Polarization: VV + VH"
    )

    print(
        "Period     : 2018-2025"
    )

    print(
        "AOI        : INDIA"
    )

    print(
        "Output     :",
        OUTPUT_FILE
    )

    print("=" * 70)

    for year in range(
        START_YEAR,
        END_YEAR + 1
    ):

        print()
        print(
            f"YEAR: {year}"
        )

        for month in range(1, 13):

            if already_collected(
                year,
                month
            ):

                print(
                    f"{year}-{month:02d}: "
                    "Already collected - skipping"
                )

                continue

            print()
            print(
                "-" * 70
            )

            print(
                f"Searching {year}-{month:02d}"
            )

            try:

                rows = collect_month(
                    year,
                    month
                )

                print(
                    f"  Found {len(rows)} scenes"
                )

                save_results(rows)

            except KeyboardInterrupt:

                print()
                print(
                    "Collector stopped by user."
                )

                return

            except Exception as error:

                print(
                    f"ERROR {year}-{month:02d}: "
                    f"{error}"
                )

                print(
                    "Continuing with next month..."
                )

            time.sleep(1)

    print()
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)

    if os.path.exists(OUTPUT_FILE):

        df = pd.read_csv(
            OUTPUT_FILE
        )

        print(
            f"Unique scenes: {len(df)}"
        )

        print(
            f"Saved: {OUTPUT_FILE}"
        )


if __name__ == "__main__":
    main()