"""
Run this after you've:
  1. Activated the venv
  2. Installed requirements.txt
  3. Put your real FIRMS_MAP_KEY into backend/.env

It confirms your key is valid and that FIRMS returns hotspot rows,
before we write any FastAPI or React code.
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

MAP_KEY = os.getenv("FIRMS_MAP_KEY")
BBOX = os.getenv("FIRMS_BBOX", "76.5,15.5,81.5,19.5")
SOURCE = os.getenv("FIRMS_SOURCE", "VIIRS_SNPP_NRT")
DAY_RANGE = os.getenv("FIRMS_DAY_RANGE", "1")

if not MAP_KEY or MAP_KEY == "your_map_key_here":
    print("FIRMS_MAP_KEY is not set. Get one free at:")
    print("https://firms.modaps.eosdis.nasa.gov/api/map_key/")
    print("Then put it in backend/.env")
    sys.exit(1)

# First, check the key itself and see remaining transaction quota
status_url = f"https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={MAP_KEY}"
status_resp = requests.get(status_url, timeout=15)
print("=== MAP_KEY status ===")
print(status_resp.text)

# Then pull a small area of real hotspot data
data_url = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{MAP_KEY}/{SOURCE}/{BBOX}/{DAY_RANGE}"
)
print(f"\n=== Fetching sample hotspot data ===\n{data_url}\n")
data_resp = requests.get(data_url, timeout=30)
data_resp.raise_for_status()

lines = data_resp.text.strip().splitlines()
print(f"Rows returned (including header): {len(lines)}")
if len(lines) > 1:
    print("Header:", lines[0])
    print("Sample row:", lines[1])
else:
    print("No hotspots in this bbox/day-range right now — that's normal, not an error.")

print("\nSetup verified. FIRMS access is working.")
