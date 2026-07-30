"""
==========================================================
 India in the World — Complete Data Downloader
==========================================================
 Downloads 35+ additional indicators from:
   1. World Bank API (free, no API key needed)
   2. Our World in Data (public GitHub CSVs)
 
 Saves in SAME format as existing data:
   [{"country_code": "IND", "year": 2023, "value": 1234.5}, ...]
 
 Run: python download_all_indicators.py
==========================================================
"""

import json
import os
import time
import requests
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COUNTRIES_FILE = BASE_DIR / "countries.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Load valid country codes
with open(COUNTRIES_FILE) as f:
    countries = json.load(f)
ALL_COUNTRY_CODES = {c["country_code"] for c in countries}

# ========================================
#  WORLD BANK INDICATORS
# ========================================
# Format: "filename" : ("WB_INDICATOR_CODE", transform_function_or_None)
# transform = None means use raw value
# transform = "billions" means divide by 1e9
# transform = "round2" means round to 2 decimal places

WORLD_BANK_INDICATORS = {
    # ---- ECONOMY (new ones, existing: gdp, gdp_per_capita, gdp_ppp, annual_gdp_growth, debt_to_gdp, inflation, unemployment, gini) ----
    "fdi_net_inflows": ("BX.KLT.DINV.CD.WD", "billions"),          # Foreign Direct Investment (net inflows, billion $)
    "trade_percent_gdp": ("NE.TRD.GNFS.ZS", None),                 # Trade (% of GDP)
    "exports_percent_gdp": ("NE.EXP.GNFS.ZS", None),               # Exports of goods/services (% of GDP)
    "gross_savings_percent_gdp": ("NY.GNS.ICTR.ZS", None),         # Gross savings (% of GDP)
    "current_account_balance_percent_gdp": ("BN.CAB.XOKA.GD.ZS", None),  # Current account balance (% of GDP)
    
    # ---- TECHNOLOGY ----
    "internet_users_percent": ("IT.NET.USER.ZS", None),             # Individuals using the Internet (% of population)
    "mobile_subscriptions_per100": ("IT.CEL.SETS.P2", None),        # Mobile cellular subscriptions (per 100 people)
    "fixed_broadband_per100": ("IT.NET.BBND.P2", None),             # Fixed broadband subscriptions (per 100 people)
    "rd_expenditure_percent_gdp": ("GB.XPD.RSDV.GD.ZS", None),     # R&D expenditure (% of GDP)
    "patent_applications_residents": ("IP.PAT.RESD", None),         # Patent applications by residents
    "trademark_applications": ("IP.TMK.TOTL", None),                # Trademark applications total
    "hightech_exports_percent": ("TX.VAL.TECH.MF.ZS", None),       # High-technology exports (% of manufactured exports)
    "ict_goods_exports_percent": ("TX.VAL.ICTG.ZS.UN", None),      # ICT goods exports (% of total goods exports)
    
    # ---- EDUCATION ----
    "education_expenditure_percent_gdp": ("SE.XPD.TOTL.GD.ZS", None),  # Govt expenditure on education (% of GDP)
    "literacy_rate_adult": ("SE.ADT.LITR.ZS", None),                   # Literacy rate, adult total (%)
    "literacy_rate_youth": ("SE.ADT.1524.LT.ZS", None),                # Literacy rate, youth total (%)
    "school_enrollment_primary": ("SE.PRM.ENRR", None),                 # School enrollment, primary (% gross)
    "school_enrollment_secondary": ("SE.SEC.ENRR", None),               # School enrollment, secondary (% gross)
    "school_enrollment_tertiary": ("SE.TER.ENRR", None),                # School enrollment, tertiary (% gross)
    "pupil_teacher_ratio_primary": ("SE.PRM.ENRL.TC.ZS", None),        # Pupil-teacher ratio, primary
    
    # ---- HEALTHCARE ----
    "hospital_beds_per1000": ("SH.MED.BEDS.ZS", None),             # Hospital beds (per 1,000 people)
    "physicians_per1000": ("SH.MED.PHYS.ZS", None),                # Physicians (per 1,000 people)
    "nurses_midwives_per1000": ("SH.MED.NUMW.P3", None),           # Nurses and midwives (per 1,000 people)
    "health_expenditure_percent_gdp": ("SH.XPD.CHEX.GD.ZS", None), # Current health expenditure (% of GDP)
    "health_expenditure_per_capita": ("SH.XPD.CHEX.PC.CD", None),   # Current health expenditure per capita ($)
    "immunization_measles": ("SH.IMM.MEAS", None),                  # Immunization, measles (% of children ages 12-23 months)
    "immunization_dpt": ("SH.IMM.IDPT", None),                      # Immunization, DPT (% of children ages 12-23 months)
    "mortality_rate_under5": ("SH.DYN.MORT", None),                 # Mortality rate, under-5 (per 1,000 live births)
    "maternal_mortality_ratio": ("SH.STA.MMRT", None),              # Maternal mortality ratio (per 100,000 live births)
    "birth_rate": ("SP.DYN.CBRT.IN", None),                         # Birth rate, crude (per 1,000 people)
    "death_rate": ("SP.DYN.CDRT.IN", None),                         # Death rate, crude (per 1,000 people)
    
    # ---- ENVIRONMENT ----
    "co2_emissions_per_capita": ("EN.ATM.CO2E.PC", None),           # CO2 emissions (metric tons per capita)
    "co2_emissions_total": ("EN.ATM.CO2E.KT", None),                # CO2 emissions (kt)
    "forest_area_percent": ("AG.LND.FRST.ZS", None),               # Forest area (% of land area)
    "renewable_energy_percent": ("EG.FEC.RNEW.ZS", None),          # Renewable energy consumption (% of total)
    "access_to_electricity": ("EG.ELC.ACCS.ZS", None),             # Access to electricity (% of population)
    "pm25_air_pollution": ("EN.ATM.PM25.MC.M3", None),              # PM2.5 air pollution, mean annual exposure
    "renewable_electricity_output": ("EG.ELC.RNEW.ZS", None),      # Renewable electricity output (% of total)
    "arable_land_percent": ("AG.LND.ARBL.ZS", None),               # Arable land (% of land area)
    
    # ---- SAFETY ----
    "military_expenditure_percent_gdp": ("MS.MIL.XPND.GD.ZS", None),  # Military expenditure (% of GDP)
    "military_expenditure_total": ("MS.MIL.XPND.CD", "billions"),      # Military expenditure (current USD, billions)
    "refugee_population_origin": ("SM.POP.REFG.OR", None),             # Refugee population by country of origin
    
    # ---- EQUALITY ----
    "female_labor_force_participation": ("SL.TLF.CACT.FE.ZS", None),   # Female labor force participation rate (%)
    "women_in_parliament": ("SG.GEN.PARL.ZS", None),                   # Women in national parliaments (%)
    "female_enrollment_tertiary": ("SE.TER.ENRR.FE", None),            # School enrollment, tertiary, female (% gross)
    
    # ---- GOVERNANCE (new ones, existing: corruption, press_freedom, democracy_index) ----
    "government_effectiveness": ("GE.EST", None),                   # Government Effectiveness Index
    "regulatory_quality": ("RQ.EST", None),                          # Regulatory Quality Index
    "rule_of_law": ("RL.EST", None),                                 # Rule of Law Index
    "voice_accountability": ("VA.EST", None),                        # Voice and Accountability Index
    "political_stability": ("PV.EST", None),                         # Political Stability Index
    
    # ---- DIGITAL / INFRASTRUCTURE ----
    "secure_internet_servers_per_million": ("IT.NET.SECR.P6", None),   # Secure Internet servers (per 1 million people)
    "access_to_clean_fuels": ("EG.CFT.ACCS.ZS", None),                # Access to clean fuels (% of population)
    "water_access_safe": ("SH.H2O.SMDW.ZS", None),                    # People using safely managed drinking water (%)
    "sanitation_access_safe": ("SH.STA.SMSS.ZS", None),               # People using safely managed sanitation (%)
    
    # ---- NEW: Additional indicators ----
    "population_growth_rate": ("SP.POP.GROW", None),                   # Population growth (annual %)
    "uhc_service_coverage": ("SH.UHC.SRVS.CV.XD", None),             # UHC service coverage index
    "logistics_performance_index": ("LP.LPI.OVRL.XQ", None),         # Logistics Performance Index (overall)
    "consumer_price_index": ("FP.CPI.TOTL", None),                    # Consumer Price Index (2010=100)
}


# ========================================
#  OUR WORLD IN DATA INDICATORS  
# ========================================
# Format: "filename": ("csv_url", "value_column_name", optional_rename_dict)

OUR_WORLD_IN_DATA_INDICATORS = {
    # ---- ENVIRONMENT ----
    "share_electricity_renewables": (
        "https://ourworldindata.org/grapher/share-electricity-renewables.csv?v=1&csvType=full&useColumnShortNames=true",
        "renewables__pct_electricity",
        {}
    ),
    "greenhouse_gas_emissions_per_capita": (
        "https://ourworldindata.org/grapher/ghg-emissions-per-capita.csv?v=1&csvType=full&useColumnShortNames=true",
        "total_ghg_emissions_per_capita",
        {}
    ),
    
    # ---- SOCIETY ----
    "poverty_ratio": (
        "https://ourworldindata.org/grapher/share-of-population-in-extreme-poverty.csv?v=1&csvType=full&useColumnShortNames=true",
        "headcount_ratio_international_povline",
        {}
    ),
    "child_mortality": (
        "https://ourworldindata.org/grapher/child-mortality.csv?v=1&csvType=full&useColumnShortNames=true",
        "obs_value__indicator__cme_mrm0",
        {}
    ),
    
    # ---- EDUCATION ----
    "learning_adjusted_years_of_school": (
        "https://ourworldindata.org/grapher/learning-adjusted-years-of-school-lays.csv?v=1&csvType=full&useColumnShortNames=true",
        "learning_adjusted_years_of_school",
        {}
    ),
    
    # ---- TECHNOLOGY ----
    "share_using_internet": (
        "https://ourworldindata.org/grapher/share-of-individuals-using-the-internet.csv?v=1&csvType=full&useColumnShortNames=true",
        "it_net_user_zs",
        {}
    ),
    
    # ---- SAFETY ----
    "terrorism_deaths": (
        "https://ourworldindata.org/grapher/fatalities-from-terrorism.csv?v=1&csvType=full&useColumnShortNames=true",
        "fatalities__terrorism__all_attacks",
        {}
    ),
    
    # ---- HEALTHCARE ----
    "share_deaths_air_pollution": (
        "https://ourworldindata.org/grapher/share-deaths-air-pollution.csv?v=1&csvType=full&useColumnShortNames=true",
        "death_rate_from_air_pollution__pct",
        {}
    ),
}


def download_world_bank(indicator_name, wb_code, transform=None):
    """Download a single indicator from World Bank API."""
    url = f"https://api.worldbank.org/v2/country/all/indicator/{wb_code}?format=json&per_page=30000"
    
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
        
        if len(json_data) < 2 or json_data[1] is None:
            print(f"  ⚠️  No data returned for {indicator_name} ({wb_code})")
            return None
        
        records = []
        for item in json_data[1]:
            code = item.get("countryiso3code", "")
            if code not in ALL_COUNTRY_CODES:
                continue
            
            year = int(item["date"])
            value = item["value"]
            
            if value is not None:
                if transform == "billions":
                    value = round(value / 1e9, 3)
                elif transform == "round2":
                    value = round(value, 2)
                else:
                    value = round(value, 3) if isinstance(value, float) else value
            
            records.append({
                "country_code": code,
                "year": year,
                "value": value
            })
        
        return records
    
    except Exception as e:
        print(f"  ❌ Error downloading {indicator_name}: {e}")
        return None


def download_owid(indicator_name, csv_url, value_column, renames=None):
    """Download a single indicator from Our World in Data CSV."""
    try:
        import pandas as pd
    except ImportError:
        print("  ❌ pandas not installed. Run: pip install pandas")
        return None
    
    try:
        df = pd.read_csv(
            csv_url,
            storage_options={'User-Agent': 'India-Global-Dashboard/1.0'}
        )
        
        # Standard OWID format has 'code' and 'year' columns
        if 'code' not in df.columns:
            print(f"  ⚠️  'code' column not found in {indicator_name}. Columns: {list(df.columns)}")
            return None
        
        if value_column not in df.columns:
            # Try to find a matching column
            possible = [c for c in df.columns if c not in ['entity', 'code', 'year', 'owid_region', 'Entity', 'Code', 'Year']]
            print(f"  ⚠️  Column '{value_column}' not found in {indicator_name}.")
            print(f"      Available columns: {possible}")
            if len(possible) == 1:
                value_column = possible[0]
                print(f"      Using: {value_column}")
            else:
                return None
        
        df = df.rename(columns={"code": "country_code"})
        df = df.dropna(subset=["country_code", "year"])
        df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
        df["value"] = pd.to_numeric(df[value_column], errors='coerce').round(3)
        df = df.dropna(subset=["value"])
        df["year"] = df["year"].astype(int)
        
        records = df[["country_code", "year", "value"]].to_dict("records")
        return records
    
    except Exception as e:
        print(f"  ❌ Error downloading {indicator_name}: {e}")
        return None


def save_data(filename, records):
    """Save records to JSON file."""
    filepath = DATA_DIR / f"{filename}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    return filepath


def main():
    # Fix Windows console encoding
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("  India in the World - Data Downloader")
    print("=" * 60)
    print()
    
    # Check existing files
    existing = {f.stem for f in DATA_DIR.glob("*.json")}
    print(f"📂 Existing data files: {len(existing)}")
    print(f"📂 Data directory: {DATA_DIR}")
    print()
    
    # ---- Download World Bank indicators ----
    total_wb = len(WORLD_BANK_INDICATORS)
    print(f"🏦 Downloading {total_wb} World Bank indicators...")
    print("-" * 50)
    
    wb_success = 0
    wb_skipped = 0
    wb_failed = 0
    
    for i, (name, (wb_code, transform)) in enumerate(WORLD_BANK_INDICATORS.items(), 1):
        if name in existing:
            print(f"  [{i}/{total_wb}] ⏭️  {name} — already exists, skipping")
            wb_skipped += 1
            continue
        
        print(f"  [{i}/{total_wb}] ⬇️  Downloading {name} ({wb_code})...", end=" ", flush=True)
        
        records = download_world_bank(name, wb_code, transform)
        
        if records and len(records) > 0:
            save_data(name, records)
            print(f"✅ {len(records)} records saved")
            wb_success += 1
        else:
            print(f"❌ failed")
            wb_failed += 1
        
        # Be nice to the API — small delay
        time.sleep(0.5)
    
    print()
    print(f"🏦 World Bank: {wb_success} downloaded, {wb_skipped} skipped, {wb_failed} failed")
    print()
    
    # ---- Download Our World in Data indicators ----
    total_owid = len(OUR_WORLD_IN_DATA_INDICATORS)
    print(f"🌍 Downloading {total_owid} Our World in Data indicators...")
    print("-" * 50)
    
    owid_success = 0
    owid_skipped = 0
    owid_failed = 0
    
    for i, (name, (csv_url, value_col, renames)) in enumerate(OUR_WORLD_IN_DATA_INDICATORS.items(), 1):
        if name in existing:
            print(f"  [{i}/{total_owid}] ⏭️  {name} — already exists, skipping")
            owid_skipped += 1
            continue
        
        print(f"  [{i}/{total_owid}] ⬇️  Downloading {name}...", end=" ", flush=True)
        
        records = download_owid(name, csv_url, value_col, renames)
        
        if records and len(records) > 0:
            save_data(name, records)
            print(f"✅ {len(records)} records saved")
            owid_success += 1
        else:
            print(f"❌ failed")
            owid_failed += 1
        
        time.sleep(0.3)
    
    print()
    print(f"🌍 OWID: {owid_success} downloaded, {owid_skipped} skipped, {owid_failed} failed")
    print()
    
    # ---- Final Summary ----
    final_count = len(list(DATA_DIR.glob("*.json")))
    print("=" * 60)
    print(f"  ✅ DONE! Total data files now: {final_count}")
    print(f"  📂 Location: {DATA_DIR}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: python create_database.py")
    print("     (This will rebuild the SQLite database with all indicators)")
    print("  2. The dashboard will automatically pick up all indicators!")


if __name__ == "__main__":
    main()
