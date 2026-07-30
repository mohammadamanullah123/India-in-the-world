"""
Download governance indicators + additional OWID indicators with corrected URLs.
Tries multiple URL patterns for each indicator.
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


def download_wb_v2(name, wb_code):
    """Download from World Bank API v2 with multiple source attempts."""
    print(f"  ⬇️  WB: {name} ({wb_code})...", end=" ", flush=True)
    
    # Try different sources (3 = WGI, 2 = WDI default)
    for source in [3, 2, None]:
        source_param = f"&source={source}" if source else ""
        url = f"https://api.worldbank.org/v2/country/all/indicator/{wb_code}?format=json&per_page=30000&date=1960:2025{source_param}"
        
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            json_data = resp.json()
            
            if len(json_data) < 2 or json_data[1] is None:
                continue
            
            records = []
            for item in json_data[1]:
                code = item.get("countryiso3code", "")
                if not code or code not in ALL_COUNTRY_CODES:
                    continue
                try:
                    year = int(item["date"])
                except:
                    continue
                value = item["value"]
                if value is not None:
                    value = round(value, 3) if isinstance(value, float) else value
                    records.append({"country_code": code, "year": year, "value": value})
            
            if records:
                filepath = DATA_DIR / f"{name}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2)
                print(f"✅ {len(records)} records (source={source})")
                return True
        except Exception:
            continue
    
    print("❌ failed all sources")
    return False


def download_owid(name, slug):
    """Download from OWID with the exact chart slug."""
    print(f"  ⬇️  OWID: {name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
    except ImportError:
        print("❌ pandas not installed")
        return False
    
    url = f"https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full&useColumnShortNames=true"
    
    try:
        df = pd.read_csv(url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
        
        if 'code' not in df.columns:
            # Try 'Code' instead
            if 'Code' in df.columns:
                df = df.rename(columns={'Code': 'code', 'Year': 'year', 'Entity': 'entity'})
            else:
                print(f"⚠️ no 'code' column. Cols: {list(df.columns)[:5]}")
                return False
        
        # Find value column(s) - exclude metadata columns
        skip = {'entity', 'code', 'year', 'Entity', 'Code', 'Year', 'owid_region'}
        value_cols = [c for c in df.columns if c not in skip]
        
        if not value_cols:
            print("❌ no value column")
            return False
        
        value_col = value_cols[0]
        
        df = df.rename(columns={"code": "country_code"})
        df = df.dropna(subset=["country_code", "year"])
        df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
        df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
        df = df.dropna(subset=["value"])
        df["year"] = df["year"].astype(int)
        
        records = df[["country_code", "year", "value"]].to_dict("records")
        
        if records:
            filepath = DATA_DIR / f"{name}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            print(f"✅ {len(records)} records (col: {value_col})")
            return True
        else:
            print("❌ no valid records")
            return False
    except Exception as e:
        print(f"❌ {e}")
        return False


def main():
    print("=" * 60)
    print("  Additional Indicators Downloader (Round 2)")
    print("=" * 60)
    print()
    
    existing = {f.stem for f in DATA_DIR.glob("*.json")}
    print(f"📂 Existing data files: {len(existing)}")
    print()
    
    success = 0
    failed = 0
    skipped = 0
    
    # ============================================
    # WORLD BANK (with correct source parameters)
    # ============================================
    wb_indicators = {
        "government_effectiveness": "GE.EST",
        "regulatory_quality": "RQ.EST",
        "voice_accountability": "VA.EST",
        "political_stability": "PV.EST",
        "uhc_service_coverage": "SH.UHC.SRVS.CV.XD",
    }
    
    print("🏦 World Bank Governance + Additional:")
    print("-" * 50)
    for name, code in wb_indicators.items():
        if name in existing:
            print(f"  ⏭️  {name} — already exists")
            skipped += 1
            continue
        if download_wb_v2(name, code):
            success += 1
        else:
            failed += 1
        time.sleep(0.5)
    
    print()
    
    # ============================================
    # OWID - Try many possible chart slugs
    # ============================================
    owid_indicators = {
        # Governance
        "egovernment_index": [
            "un-e-government-index",
            "e-government-development-index-egdi",
            "e-gov-development-index",
        ],
        "eparticipation_index": [
            "un-e-participation-index",
            "e-participation-index-epi",
        ],
        # Economy
        "economic_freedom_index": [
            "economic-freedom",
            "human-freedom-index",
            "index-of-economic-freedom",
            "economic-freedom-overall-index",
        ],
        # Environment
        "environmental_performance_index": [
            "environmental-performance-index-epi",
            "epi-score",
            "yale-environmental-performance-index",
        ],
        "climate_risk_index": [
            "climate-risk-index",
            "germanwatch-climate-risk-index",
            "inform-risk-index",
        ],
        # Society
        "social_progress_index": [
            "social-progress-index-spi",
            "social-progress-index-overall",
        ],
        # Safety
        "global_peace_index": [
            "peace-index",
            "gpi-overall-score",
            "global-peace-index-score",
        ],
        "road_safety_deaths": [
            "death-rate-road-injuries",
            "road-death-rate",
            "road-traffic-death-rate-who",
            "death-rates-road-incidents",
        ],
        # Equality
        "global_gender_gap_index": [
            "global-gender-gap-index-wef",
            "gender-gap-index-wef",
            "wef-gender-gap-index",
        ],
        # Tech
        "global_innovation_index": [
            "wipo-global-innovation-index",
            "innovation-index",
        ],
        "global_cybersecurity_index": [
            "cybersecurity-index",
            "itu-cybersecurity-index",
            "national-cyber-security-index",
        ],
        # Digital Govt
        "sdg_index_score": [
            "sustainable-development-index",
            "sdg-index",
            "sdsn-sdg-index",
        ],
        # Environment
        "water_stress_index": [
            "freshwater-withdrawals-as-a-share-of-internal-resources",
            "water-withdrawals-as-share-of-renewable-water",
            "level-of-water-stress",
        ],
    }
    
    print("🌍 OWID - Trying multiple URL patterns:")
    print("-" * 50)
    for name, slugs in owid_indicators.items():
        if name in existing:
            print(f"  ⏭️  {name} — already exists")
            skipped += 1
            continue
        
        found = False
        for slug in slugs:
            if download_owid(name, slug):
                success += 1
                found = True
                break
            time.sleep(0.3)
        
        if not found:
            failed += 1
        time.sleep(0.3)
    
    print()
    print("=" * 60)
    print(f"  ✅ Downloaded: {success}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📂 Total data files: {len(list(DATA_DIR.glob('*.json')))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
