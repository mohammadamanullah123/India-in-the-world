"""
Download World Bank Governance Indicators (WGI).
These use indicator codes like GE.EST, RQ.EST, VA.EST, PV.EST
which require a slightly different API call with source=3 parameter.
"""
import json
import sys
import io
import time
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COUNTRIES_FILE = BASE_DIR / "countries.json"

with open(COUNTRIES_FILE) as f:
    countries = json.load(f)
ALL_COUNTRY_CODES = {c["country_code"] for c in countries}

GOVERNANCE_INDICATORS = {
    "government_effectiveness": "GE.EST",
    "regulatory_quality": "RQ.EST",
    "voice_accountability": "VA.EST",
    "political_stability": "PV.EST",
}

def download_wb_governance(name, wb_code):
    """Download from World Bank WGI using source=3 parameter."""
    # Try with source parameter for WGI data
    urls = [
        f"https://api.worldbank.org/v2/country/all/indicator/{wb_code}?format=json&per_page=30000&source=3",
        f"https://api.worldbank.org/v2/country/all/indicator/{wb_code}?format=json&per_page=30000&date=1996:2025",
        f"https://api.worldbank.org/v2/country/all/indicator/{wb_code}?format=json&per_page=30000",
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            json_data = resp.json()
            
            if len(json_data) < 2 or json_data[1] is None:
                continue
            
            records = []
            for item in json_data[1]:
                code = item.get("countryiso3code", "")
                if code not in ALL_COUNTRY_CODES:
                    continue
                year = int(item["date"])
                value = item["value"]
                if value is not None:
                    value = round(value, 3)
                    records.append({"country_code": code, "year": year, "value": value})
            
            if records:
                return records
        except Exception as e:
            continue
    
    return None


def main():
    print("=" * 60)
    print("  World Bank Governance Indicators (WGI)")
    print("=" * 60)
    print()
    
    existing = {f.stem for f in DATA_DIR.glob("*.json")}
    
    for name, wb_code in GOVERNANCE_INDICATORS.items():
        if name in existing:
            print(f"  ⏭️  {name} — already exists, skipping")
            continue
        
        print(f"  ⬇️  Downloading {name} ({wb_code})...", end=" ", flush=True)
        records = download_wb_governance(name, wb_code)
        
        if records:
            filepath = DATA_DIR / f"{name}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            print(f"✅ {len(records)} records saved")
        else:
            print("❌ failed")
        
        time.sleep(0.5)
    
    print()
    print(f"📂 Total data files: {len(list(DATA_DIR.glob('*.json')))}")


if __name__ == "__main__":
    main()
