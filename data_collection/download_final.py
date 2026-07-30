"""
Robust downloader for WB governance indicators + OWID indicators.
Uses proper delays and error handling.
"""
import json, sys, io, time, requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COUNTRIES_FILE = BASE_DIR / "countries.json"

with open(COUNTRIES_FILE) as f:
    countries = json.load(f)
ALL_CODES = {c["country_code"] for c in countries}

def save(name, records):
    filepath = DATA_DIR / f"{name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

def wb_download(name, code, source=None):
    """Download from World Bank with retry logic."""
    print(f"\n{'='*50}")
    print(f"Downloading: {name} ({code})")
    
    for attempt in range(3):
        src_param = f"&source={source}" if source else ""
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=30000&date=1960:2025{src_param}"
        
        try:
            if attempt > 0:
                wait = 5 * attempt
                print(f"  Retry {attempt}, waiting {wait}s...")
                time.sleep(wait)
            
            resp = requests.get(url, timeout=60, headers={'User-Agent': 'Mozilla/5.0'})
            print(f"  HTTP status: {resp.status_code}")
            
            if resp.status_code == 429:
                print("  Rate limited! Waiting 30s...")
                time.sleep(30)
                continue
            
            resp.raise_for_status()
            data = resp.json()
            
            if len(data) < 2 or data[1] is None:
                print(f"  No data in response (len={len(data)})")
                if source is None:
                    # Try with source=3 for WGI
                    return wb_download(name, code, source=3)
                continue
            
            records = []
            for item in data[1]:
                c = item.get("countryiso3code", "")
                if c not in ALL_CODES:
                    continue
                try:
                    year = int(item["date"])
                except:
                    continue
                val = item["value"]
                if val is not None:
                    val = round(val, 3) if isinstance(val, float) else val
                    records.append({"country_code": c, "year": year, "value": val})
            
            if records:
                save(name, records)
                print(f"  ✅ Saved {len(records)} records")
                return True
            else:
                print(f"  No valid records found")
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"  ❌ All attempts failed for {name}")
    return False

def owid_download(name, slug):
    """Download from OWID."""
    print(f"\n{'='*50}")
    print(f"Downloading: {name} (OWID: {slug})")
    
    try:
        import pandas as pd
        url = f"https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full&useColumnShortNames=true"
        df = pd.read_csv(url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
        
        if 'code' not in df.columns:
            print(f"  No 'code' column. Cols: {list(df.columns)[:5]}")
            return False
        
        skip = {'entity', 'code', 'year', 'Entity', 'Code', 'Year', 'owid_region'}
        value_cols = [c for c in df.columns if c not in skip]
        if not value_cols:
            return False
        
        val_col = value_cols[0]
        print(f"  Value column: {val_col}")
        
        df = df.rename(columns={"code": "country_code"})
        df = df.dropna(subset=["country_code", "year"])
        df = df[df["country_code"].isin(ALL_CODES)]
        df["value"] = pd.to_numeric(df[val_col], errors='coerce').round(3)
        df = df.dropna(subset=["value"])
        df["year"] = df["year"].astype(int)
        
        records = df[["country_code", "year", "value"]].to_dict("records")
        if records:
            save(name, records)
            print(f"  ✅ Saved {len(records)} records")
            return True
    except Exception as e:
        print(f"  ❌ {e}")
    return False

def main():
    print("ROBUST DOWNLOADER - Sequential with delays")
    print("=" * 60)
    
    existing = {f.stem for f in DATA_DIR.glob("*.json")}
    success = 0
    
    # World Bank Governance (WGI source=3)
    wb_items = [
        ("government_effectiveness", "GE.EST", 3),
        ("regulatory_quality", "RQ.EST", 3),
        ("voice_accountability", "VA.EST", 3),
        ("political_stability", "PV.EST", 3),
        ("uhc_service_coverage", "SH.UHC.SRVS.CV.XD", 3),
    ]
    
    for name, code, src in wb_items:
        if name in existing:
            print(f"\n⏭️  {name} — exists")
            continue
        if wb_download(name, code, source=src):
            success += 1
        time.sleep(3)  # Be nice to API
    
    # OWID indicators
    owid_items = [
        ("economic_freedom_index", "human-freedom-index"),
        ("road_safety_deaths", "death-rates-road-incidents"),
        ("global_cybersecurity_index", "national-cyber-security-index"),
    ]
    
    for name, slug in owid_items:
        if name in existing:
            print(f"\n⏭️  {name} — exists")
            continue
        if owid_download(name, slug):
            success += 1
        time.sleep(2)
    
    print(f"\n\n{'='*60}")
    print(f"Done! Downloaded: {success}")
    print(f"Total files: {len(list(DATA_DIR.glob('*.json')))}")

if __name__ == "__main__":
    main()
