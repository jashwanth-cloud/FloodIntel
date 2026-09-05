import requests
from pathlib import Path

# ============================================================
# GROWRISEMIND — SENTINEL-1 FLOOD AOI EXTRACTION
# ============================================================

TOKEN_FILE = Path("cdse_token.txt")
OUTPUT_DIR = Path("flood_aoi")

PROCESS_URL = "https://sh.dataspace.copernicus.eu/process/v1"

# ------------------------------------------------------------
# Target AOI
# ------------------------------------------------------------

LAT = 16.3067
LON = 80.4365
HALF_SIZE = 0.05

WEST = LON - HALF_SIZE
SOUTH = LAT - HALF_SIZE
EAST = LON + HALF_SIZE
NORTH = LAT + HALF_SIZE

# ------------------------------------------------------------
# Selected Sentinel-1 scenes from our metadata analysis
# ------------------------------------------------------------

SCENES = {
    "before": {
        "date": "2024-08-20",
        "from": "2024-08-20T00:00:00Z",
        "to": "2024-08-21T00:00:00Z",
    },
    "after": {
        "date": "2024-09-01",
        "from": "2024-09-01T00:00:00Z",
        "to": "2024-09-02T00:00:00Z",
    },
}

OUTPUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Load token
# ------------------------------------------------------------

if not TOKEN_FILE.exists():
    raise FileNotFoundError(
        "cdse_token.txt not found."
    )

token = TOKEN_FILE.read_text().strip()

if not token:
    raise ValueError(
        "cdse_token.txt is empty."
    )

headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
}

# ------------------------------------------------------------
# Evalscript
# ------------------------------------------------------------

EVALSCRIPT = """
//VERSION=3

function setup() {
    return {
        input: ["VV", "VH"],
        output: {
            bands: 2,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(samples) {
    return [
        samples.VV,
        samples.VH
    ];
}
"""

# ------------------------------------------------------------
# Request function
# ------------------------------------------------------------

def request_scene(role, date_from, date_to):

    print()
    print("=" * 70)
    print(f"EXTRACTING {role.upper()} SCENE")
    print("=" * 70)

    request_body = {
        "input": {
            "bounds": {
                "bbox": [
                    WEST,
                    SOUTH,
                    EAST,
                    NORTH
                ]
            },

            "data": [
                {
                    "type": "sentinel-1-grd",

                    "dataFilter": {
                        "timeRange": {
                            "from": date_from,
                            "to": date_to
                        },

                        "orbitDirection": "DESCENDING",

                        "polarization": "DV"
                    }
                }
            ]
        },

        "output": {
            "width": 512,
            "height": 512,

            "responses": [
                {
                    "identifier": "default",

                    "format": {
                        "type": "image/tiff"
                    }
                }
            ]
        },

        "evalscript": EVALSCRIPT
    }

    print("AOI:")
    print("  West :", WEST)
    print("  South:", SOUTH)
    print("  East :", EAST)
    print("  North:", NORTH)

    print()
    print("Date:")
    print(" ", date_from)
    print(" ", date_to)

    print()
    print("Requesting VV + VH...")
    print("Resolution:", "512 x 512")

    try:

        response = requests.post(
            PROCESS_URL,
            json=request_body,
            headers=headers,
            timeout=(20, 180)
        )

        print()
        print("HTTP:", response.status_code)
        print(
            "Content-Type:",
            response.headers.get("Content-Type")
        )

        print(
            "Bytes received:",
            len(response.content)
        )

        if response.status_code != 200:

            print()
            print("ERROR:")
            print(response.text[:3000])

            return False

        output_file = (
            OUTPUT_DIR /
            f"{role}_vv_vh.tiff"
        )

        output_file.write_bytes(
            response.content
        )

        print()
        print("SUCCESS")
        print("Saved:", output_file)
        print(
            "Size:",
            round(
                output_file.stat().st_size
                / 1024,
                2
            ),
            "KB"
        )

        return True

    except requests.exceptions.Timeout:

        print()
        print("ERROR: Request timed out.")

        return False

    except Exception as e:

        print()
        print("ERROR:")
        print(e)

        return False


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("GROWRISEMIND — SENTINEL-1 FLOOD AOI EXTRACTION")
print("=" * 70)

print()
print("CDSE token loaded.")
print("Token length:", len(token))

print()
print("Selected scenes:")
print("  BEFORE:", SCENES["before"]["date"])
print("  AFTER :", SCENES["after"]["date"])

print()
print("Polarizations: VV + VH")

# ------------------------------------------------------------
# BEFORE
# ------------------------------------------------------------

before_success = request_scene(
    "before",
    SCENES["before"]["from"],
    SCENES["before"]["to"]
)

# ------------------------------------------------------------
# AFTER
# ------------------------------------------------------------

after_success = request_scene(
    "after",
    SCENES["after"]["from"],
    SCENES["after"]["to"]
)

# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("AOI EXTRACTION COMPLETE")
print("=" * 70)

print()

if before_success and after_success:

    print("Before scene: SUCCESS")
    print("After scene : SUCCESS")

    print()
    print("Generated files:")

    for file in sorted(
        OUTPUT_DIR.glob("*.tiff")
    ):

        size_kb = (
            file.stat().st_size
            / 1024
        )

        print(
            f"  {file.name:25s}"
            f"{size_kb:10.2f} KB"
        )

    print()
    print("READY FOR FLOOD CHANGE ANALYSIS.")

else:

    print("AOI extraction was not fully successful.")

    if not before_success:
        print("  BEFORE extraction failed.")

    if not after_success:
        print("  AFTER extraction failed.")