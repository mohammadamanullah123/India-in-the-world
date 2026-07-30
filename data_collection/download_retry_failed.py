"""
Retry failed indicators with corrected codes and longer timeouts.
"""
import json
import sys
import io
import time
import requests
import pandas as pd
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
with open(BASE_DIR / "countries.json") as f:
    ALL_CODES = {c["country_code"] for c in json.load(f)}


def save(name, records):
    with open(DATA_DIR / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"  -> Saved {len(records)} records to {name}.json")


def wb_download(name, code, transform=None, timeout=60):
    """World Bank API with longer timeout."""
    url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=30000"
    print(f"  Downloading {name} ({code})...", end=" ", flush=True)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2 or data[1] is None:
            print("No data")
            return False
        records = []
        for item in data[1]:
            c = item.get("countryiso3code", "")
            if c not in ALL_CODES:
                continue
            v = item["value"]
            if v is not None:
                if transform == "billions":
                    v = round(v / 1e9, 3)
                else:
                    v = round(v, 3) if isinstance(v, float) else v
            records.append({"country_code": c, "year": int(item["date"]), "value": v})
        if records:
            save(name, records)
            return True
        print("No valid records")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def owid_download(name, csv_url, timeout=60):
    """Our World in Data CSV download."""
    print(f"  Downloading {name}...", end=" ", flush=True)
    try:
        df = pd.read_csv(csv_url, storage_options={'User-Agent': 'India-Dashboard/1.0'})
        if 'code' not in df.columns:
            print(f"No 'code' column. Cols: {list(df.columns)[:5]}")
            return False
        df = df.rename(columns={"code": "country_code"})
        df = df.dropna(subset=["country_code", "year"])
        df = df[df["country_code"].isin(ALL_CODES)]
        # Find the value column (exclude metadata columns)
        skip = {'entity', 'code', 'country_code', 'year', 'owid_region', 'Entity', 'Code', 'Year'}
        val_cols = [c for c in df.columns if c not in skip]
        if not val_cols:
            print("No value columns found")
            return False
        val_col = val_cols[0]
        print(f"(using col: {val_col})", end=" ")
        df["value"] = pd.to_numeric(df[val_col], errors='coerce').round(3)
        df = df.dropna(subset=["value"])
        df["year"] = df["year"].astype(int)
        records = df[["country_code", "year", "value"]].to_dict("records")
        if records:
            save(name, records)
            return True
        print("No valid records")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("=" * 60)
    print("  Retry Failed Indicators")
    print("=" * 60)
    print()
    
    success = 0
    failed = 0
    
    # 1. World Bank timeouts - retry with 60s timeout
    print("[World Bank - Timeout Retries]")
    for name, code, transform in [
        ("hightech_exports_percent", "TX.VAL.TECH.MF.ZS", None),
        ("ict_goods_exports_percent", "TX.VAL.ICTG.ZS.UN", None),
        ("literacy_rate_youth", "SE.ADT.1524.LT.ZS", None),
        ("health_expenditure_percent_gdp", "SH.XPD.CHEX.GD.ZS", None),
    ]:
        if (DATA_DIR / f"{name}.json").exists():
            print(f"  {name} already exists, skipping")
            continue
        if wb_download(name, code, transform, timeout=60):
            success += 1
        else:
            failed += 1
        time.sleep(1)
    
    print()
    
    # 2. Governance indicators - use source=2 parameter for WGI database
    print("[World Bank - Governance Indicators (WGI source)]")
    gov_indicators = [
        ("government_effectiveness", "GE.EST"),
        ("regulatory_quality", "RQ.EST"),
        ("rule_of_law", "RL.EST"),
        ("voice_accountability", "VA.EST"),
        ("political_stability", "PV.EST"),
    ]
    for name, code in gov_indicators:
        if (DATA_DIR / f"{name}.json").exists():
            print(f"  {name} already exists, skipping")
            continue
        # Try with source=2 (WGI database)
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=30000&source=2"
        print(f"  Downloading {name} ({code}, source=2)...", end=" ", flush=True)
        try:
            resp = requests.get(url, timeout=60)
            data = resp.json()
            if len(data) >= 2 and data[1]:
                records = []
                for item in data[1]:
                    c = item.get("countryiso3code") or item.get("country", {}).get("id", "")
                    if c not in ALL_CODES:
                        continue
                    v = item["value"]
                    if v is not None:
                        v = round(v, 3) if isinstance(v, float) else v
                    records.append({"country_code": c, "year": int(item["date"]), "value": v})
                if records:
                    save(name, records)
                    success += 1
                else:
                    print("No valid records")
                    failed += 1
            else:
                print("No data returned")
                failed += 1
        except Exception as e:
            print(f"Error: {e}")
            failed += 1
        time.sleep(1)
    
    print()
    
    # 3. CO2 data from Our World in Data (World Bank deprecated these)
    print("[Our World in Data - CO2 & Others]")
    owid_retry = [
        ("co2_emissions_per_capita", 
         "https://ourworldindata.org/grapher/co-emissions-per-capita.csv?v=1&csvType=full&useColumnShortNames=true"),
        ("co2_emissions_total",
         "https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv?v=1&csvType=full&useColumnShortNames=true"),
        ("poverty_ratio",
         "https://ourworldindata.org/grapher/share-of-population-in-extreme-poverty.csv?v=1&csvType=full&useColumnShortNames=true"),
        ("share_deaths_air_pollution",
         "https://ourworldindata.org/grapher/death-rates-from-air-pollution.csv?v=1&csvType=full&useColumnShortNames=true"),
    ]
    for name, url in owid_retry:
        if (DATA_DIR / f"{name}.json").exists():
            print(f"  {name} already exists, skipping")
            continue
        if owid_download(name, url):
            success += 1
        else:
            failed += 1
        time.sleep(0.5)
    
    print()
    
    # 4. Additional useful indicators from OWID
    print("[Our World in Data - Additional Indicators]")
    extra_owid = [
        ("human_rights_score",
         "https://ourworldindata.org/grapher/human-rights-scores.csv?v=1&csvType=full&useColumnShortNames=true"),
        ("nuclear_energy_share",
         "https://ourworldindata.org/grapher/share-electricity-nuclear.csv?v=1&csvType=full&useColumnShortNames=true"),
        ("renewable_energy_share_total",
         "https://ourworldindata.org/grapher/renewable-share-energy.csv?v=1&csvType=full&useColumnShortNames=true"),
    ]
    for name, url in extra_owid:
        if (DATA_DIR / f"{name}.json").exists():
            print(f"  {name} already exists, skipping")
            continue
        if owid_download(name, url):
            success += 1
        else:
            failed += 1
        time.sleep(0.5)
    
    print()
    final = len(list(DATA_DIR.glob("*.json")))
    print("=" * 60)
    print(f"  Retry: {success} succeeded, {failed} failed")
    print(f"  Total data files now: {final}")
    print("=" * 60)


if __name__ == "__main__":
    main()
