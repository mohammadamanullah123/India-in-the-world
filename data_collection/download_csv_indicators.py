"""
==========================================================
 CSV-Based Indicators Downloader
==========================================================
 Downloads indicators that are available as CSV/Excel
 from various sources (not via World Bank API or OWID).
 
 Sources:
   - Heritage Foundation (Economic Freedom Index)
   - Yale CIESIN (Environmental Performance Index)
   - Social Progress Imperative
   - Institute for Economics & Peace (Global Peace Index)
   - UN DESA (E-Government, E-Participation)
   - OECD (PISA Rankings)
   - World Economic Forum (Global Gender Gap)
   - ITU (Global Cybersecurity Index)
   - World Bank (Human Capital Index)
   - Open Data Watch (Open Data Inventory)
 
 Run: python download_csv_indicators.py
==========================================================
"""

import json
import os
import sys
import io
import time
import requests
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COUNTRIES_FILE = BASE_DIR / "countries.json"

DATA_DIR.mkdir(exist_ok=True)

# Load valid country codes
with open(COUNTRIES_FILE) as f:
    countries_list = json.load(f)
ALL_COUNTRY_CODES = {c["country_code"] for c in countries_list}

# Build a name-to-code mapping for fuzzy matching
COUNTRY_NAME_TO_CODE = {}
for c in countries_list:
    name = c["country_name"].strip().lower()
    code = c["country_code"]
    COUNTRY_NAME_TO_CODE[name] = code
    # Add common variations
    COUNTRY_NAME_TO_CODE[code.lower()] = code

# Add common name mappings that differ between sources
NAME_ALIASES = {
    "united states of america": "USA",
    "united states": "USA",
    "us": "USA",
    "usa": "USA",
    "uk": "GBR",
    "united kingdom of great britain and northern ireland": "GBR",
    "russian federation": "RUS",
    "russia": "RUS",
    "korea, republic of": "KOR",
    "south korea": "KOR",
    "korea, rep.": "KOR",
    "republic of korea": "KOR",
    "korea (republic of)": "KOR",
    "korea (rep.)": "KOR",
    "korea, dem. people's rep.": "PRK",
    "north korea": "PRK",
    "iran, islamic republic of": "IRN",
    "iran (islamic republic of)": "IRN",
    "iran": "IRN",
    "iran, islamic rep.": "IRN",
    "venezuela, bolivarian republic of": "VEN",
    "venezuela (bolivarian republic of)": "VEN",
    "venezuela": "VEN",
    "venezuela, rb": "VEN",
    "bolivia, plurinational state of": "BOL",
    "bolivia (plurinational state of)": "BOL",
    "bolivia": "BOL",
    "tanzania, united republic of": "TZA",
    "united republic of tanzania": "TZA",
    "tanzania": "TZA",
    "viet nam": "VNM",
    "vietnam": "VNM",
    "côte d'ivoire": "CIV",
    "cote d'ivoire": "CIV",
    "ivory coast": "CIV",
    "congo, democratic republic of the": "COD",
    "democratic republic of the congo": "COD",
    "dr congo": "COD",
    "congo, dem. rep.": "COD",
    "congo, republic of the": "COG",
    "republic of the congo": "COG",
    "congo": "COG",
    "congo, rep.": "COG",
    "lao people's democratic republic": "LAO",
    "laos": "LAO",
    "lao pdr": "LAO",
    "syria": "SYR",
    "syrian arab republic": "SYR",
    "moldova, republic of": "MDA",
    "republic of moldova": "MDA",
    "moldova": "MDA",
    "north macedonia": "MKD",
    "macedonia": "MKD",
    "the former yugoslav republic of macedonia": "MKD",
    "macedonia, fyr": "MKD",
    "palestine": "PSE",
    "state of palestine": "PSE",
    "west bank and gaza": "PSE",
    "brunei darussalam": "BRN",
    "brunei": "BRN",
    "czechia": "CZE",
    "czech republic": "CZE",
    "eswatini": "SWZ",
    "swaziland": "SWZ",
    "micronesia, federated states of": "FSM",
    "micronesia (federated states of)": "FSM",
    "micronesia": "FSM",
    "cabo verde": "CPV",
    "cape verde": "CPV",
    "türkiye": "TUR",
    "turkiye": "TUR",
    "turkey": "TUR",
    "egypt": "EGY",
    "egypt, arab rep.": "EGY",
    "gambia": "GMB",
    "gambia, the": "GMB",
    "the gambia": "GMB",
    "kyrgyzstan": "KGZ",
    "kyrgyz republic": "KGZ",
    "slovakia": "SVK",
    "slovak republic": "SVK",
    "yemen": "YEM",
    "yemen, rep.": "YEM",
    "hong kong": "HKG",
    "hong kong, china": "HKG",
    "hong kong sar": "HKG",
    "hong kong sar, china": "HKG",
    "taiwan": "TWN",
    "taiwan, china": "TWN",
    "chinese taipei": "TWN",
    "macao": "MAC",
    "macao, china": "MAC",
    "macau": "MAC",
    "timor-leste": "TLS",
    "east timor": "TLS",
    "saint lucia": "LCA",
    "st. lucia": "LCA",
    "saint vincent and the grenadines": "VCT",
    "st. vincent and the grenadines": "VCT",
    "saint kitts and nevis": "KNA",
    "st. kitts and nevis": "KNA",
}

for alias, code in NAME_ALIASES.items():
    COUNTRY_NAME_TO_CODE[alias.lower()] = code


def resolve_country(name_or_code):
    """Try to resolve a country name or code to a valid ISO3 code."""
    if not name_or_code:
        return None
    
    val = str(name_or_code).strip()
    
    # Direct ISO3 match
    if val.upper() in ALL_COUNTRY_CODES:
        return val.upper()
    
    # Name lookup
    lower = val.lower()
    if lower in COUNTRY_NAME_TO_CODE:
        code = COUNTRY_NAME_TO_CODE[lower]
        if code in ALL_COUNTRY_CODES:
            return code
    
    return None


def save_data(filename, records):
    """Save records to JSON file."""
    filepath = DATA_DIR / f"{filename}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    return filepath


def download_with_pandas(url, parse_func, indicator_name):
    """Generic downloader that uses pandas to read CSV/Excel and parse."""
    try:
        import pandas as pd
    except ImportError:
        print("  ❌ pandas not installed. Run: pip install pandas")
        return None
    
    try:
        headers = {'User-Agent': 'DataOfTheWorld-Dashboard/1.0'}
        
        if url.endswith('.xlsx') or url.endswith('.xls'):
            resp = requests.get(url, headers=headers, timeout=60)
            resp.raise_for_status()
            from io import BytesIO
            df = pd.read_excel(BytesIO(resp.content))
        else:
            df = pd.read_csv(url, storage_options={'User-Agent': 'DataOfTheWorld-Dashboard/1.0'})
        
        records = parse_func(df)
        return records
    except Exception as e:
        print(f"  ❌ Error downloading {indicator_name}: {e}")
        return None


# ================================================================
#  INDICATOR DOWNLOAD FUNCTIONS
# ================================================================

def download_human_capital_index():
    """Download Human Capital Index from World Bank API."""
    indicator_name = "human_capital_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    url = "https://api.worldbank.org/v2/country/all/indicator/HD.HCI.OVRL?format=json&per_page=30000"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
        
        if len(json_data) < 2 or json_data[1] is None:
            print("⚠️  No data returned")
            return None
        
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
            save_data(indicator_name, records)
            print(f"✅ {len(records)} records saved")
        else:
            print("❌ no valid records")
        return records
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_economic_freedom_index():
    """Download Economic Freedom Index from Heritage Foundation."""
    indicator_name = "economic_freedom_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Heritage Foundation provides data via their API
        url = "https://www.heritage.org/index/pages/all-country-scores"
        # Try the direct download link
        csv_url = "https://www.heritage.org/index/csv/download"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try alternative OWID source which may have historical data
        owid_url = "https://ourworldindata.org/grapher/economic-freedom-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' not in df.columns:
                print("⚠️  'code' column not found, trying alternatives...")
                return None
            
            # Find value column
            value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
            if not value_cols:
                print("❌ no value column found")
                return None
            
            value_col = value_cols[0]
            df = df.rename(columns={"code": "country_code"})
            df = df.dropna(subset=["country_code", "year"])
            df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
            df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
            df = df.dropna(subset=["value"])
            df["year"] = df["year"].astype(int)
            
            records = df[["country_code", "year", "value"]].to_dict("records")
            
            if records:
                save_data(indicator_name, records)
                print(f"✅ {len(records)} records saved")
            else:
                print("❌ no valid records")
            return records
        except Exception:
            print("❌ OWID source not available")
            return None
            
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_epi():
    """Download Environmental Performance Index from Yale."""
    indicator_name = "environmental_performance_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID source
        owid_url = "https://ourworldindata.org/grapher/environmental-performance-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_social_progress_index():
    """Download Social Progress Index."""
    indicator_name = "social_progress_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID source
        owid_url = "https://ourworldindata.org/grapher/social-progress-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_global_peace_index():
    """Download Global Peace Index."""
    indicator_name = "global_peace_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID source (they often have this)
        owid_url = "https://ourworldindata.org/grapher/global-peace-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_egovernment_index():
    """Download E-Government Development Index from UN."""
    indicator_name = "egovernment_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID source
        owid_url = "https://ourworldindata.org/grapher/e-government-development-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_eparticipation_index():
    """Download E-Participation Index from UN."""
    indicator_name = "eparticipation_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID source
        owid_url = "https://ourworldindata.org/grapher/e-participation-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_global_gender_gap():
    """Download Global Gender Gap Index."""
    indicator_name = "global_gender_gap_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID
        owid_url = "https://ourworldindata.org/grapher/gender-gap-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_cybersecurity_index():
    """Download Global Cybersecurity Index from ITU."""
    indicator_name = "global_cybersecurity_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID
        owid_url = "https://ourworldindata.org/grapher/national-cybersecurity-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_global_innovation_index():
    """Download Global Innovation Index."""
    indicator_name = "global_innovation_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        # Try OWID - WIPO Global Innovation Index
        owid_url = "https://ourworldindata.org/grapher/global-innovation-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_climate_change_performance():
    """Download Climate Change Performance Index."""
    indicator_name = "climate_change_performance_index"
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        owid_url = "https://ourworldindata.org/grapher/climate-change-performance-index.csv?v=1&csvType=full&useColumnShortNames=true"
        
        try:
            df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
            
            if 'code' in df.columns:
                value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
                if value_cols:
                    value_col = value_cols[0]
                    df = df.rename(columns={"code": "country_code"})
                    df = df.dropna(subset=["country_code", "year"])
                    df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
                    df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
                    df = df.dropna(subset=["value"])
                    df["year"] = df["year"].astype(int)
                    
                    records = df[["country_code", "year", "value"]].to_dict("records")
                    
                    if records:
                        save_data(indicator_name, records)
                        print(f"✅ {len(records)} records saved")
                        return records
        except Exception:
            pass
        
        print("❌ source not available")
        return None
    except Exception as e:
        print(f"❌ {e}")
        return None


def download_owid_generic(indicator_name, owid_chart_slug):
    """Generic OWID downloader using chart slug."""
    print(f"  ⬇️  Downloading {indicator_name}...", end=" ", flush=True)
    
    try:
        import pandas as pd
        
        owid_url = f"https://ourworldindata.org/grapher/{owid_chart_slug}.csv?v=1&csvType=full&useColumnShortNames=true"
        
        df = pd.read_csv(owid_url, storage_options={'User-Agent': 'DataOfTheWorld/1.0'})
        
        if 'code' not in df.columns:
            print(f"⚠️  'code' column not found. Columns: {list(df.columns)}")
            return None
        
        value_cols = [c for c in df.columns if c not in ['entity', 'code', 'year', 'Entity', 'Code', 'Year']]
        if not value_cols:
            print("❌ no value column found")
            return None
        
        value_col = value_cols[0]
        print(f"(using column: {value_col}) ", end="", flush=True)
        
        df = df.rename(columns={"code": "country_code"})
        df = df.dropna(subset=["country_code", "year"])
        df = df[df["country_code"].isin(ALL_COUNTRY_CODES)]
        df["value"] = pd.to_numeric(df[value_col], errors='coerce').round(3)
        df = df.dropna(subset=["value"])
        df["year"] = df["year"].astype(int)
        
        records = df[["country_code", "year", "value"]].to_dict("records")
        
        if records:
            save_data(indicator_name, records)
            print(f"✅ {len(records)} records saved")
        else:
            print("❌ no valid records")
        return records
    except Exception as e:
        print(f"❌ {e}")
        return None


def main():
    print("=" * 60)
    print("  CSV-Based Indicators Downloader")
    print("=" * 60)
    print()
    
    existing = {f.stem for f in DATA_DIR.glob("*.json")}
    print(f"📂 Existing data files: {len(existing)}")
    print()
    
    success = 0
    failed = 0
    skipped = 0
    
    # Define all indicators to try
    # Format: (indicator_name, download_function_or_owid_slug)
    indicators = [
        # World Bank API based
        ("human_capital_index", download_human_capital_index),
        
        # OWID-based (try these chart slugs)
        ("economic_freedom_index", lambda: download_owid_generic("economic_freedom_index", "economic-freedom-of-the-world-index")),
        ("environmental_performance_index", lambda: download_owid_generic("environmental_performance_index", "environmental-performance-index")),
        ("social_progress_index", lambda: download_owid_generic("social_progress_index", "social-progress-index")),
        ("global_peace_index", lambda: download_owid_generic("global_peace_index", "global-peace-index")),
        ("global_gender_gap_index", lambda: download_owid_generic("global_gender_gap_index", "gender-gap-index")),
        ("global_innovation_index", lambda: download_owid_generic("global_innovation_index", "global-innovation-index")),
        ("global_cybersecurity_index", lambda: download_owid_generic("global_cybersecurity_index", "national-cybersecurity-index")),
        ("climate_change_performance_index", lambda: download_owid_generic("climate_change_performance_index", "climate-change-performance-index")),
        ("egovernment_index", lambda: download_owid_generic("egovernment_index", "e-government-development-index")),
        ("eparticipation_index", lambda: download_owid_generic("eparticipation_index", "e-participation-index")),
        
        # More OWID chart slugs to try
        ("water_stress_index", lambda: download_owid_generic("water_stress_index", "water-stress")),
        ("sdg_index_score", lambda: download_owid_generic("sdg_index_score", "sdg-index-score")),
        ("pisa_reading_score", lambda: download_owid_generic("pisa_reading_score", "pisa-test-score-mean-performance-on-the-reading-scale")),
        ("crime_rate", lambda: download_owid_generic("crime_rate", "homicide-rate-unodc")),
        ("disaster_risk_index", lambda: download_owid_generic("disaster_risk_index", "inform-risk-index")),
        ("road_safety_deaths", lambda: download_owid_generic("road_safety_deaths", "road-traffic-death-rate")),
    ]
    
    print(f"📋 Attempting to download {len(indicators)} indicators...")
    print("-" * 50)
    
    for name, download_func in indicators:
        if name in existing:
            print(f"  ⏭️  {name} — already exists, skipping")
            skipped += 1
            continue
        
        result = download_func()
        if result and len(result) > 0:
            success += 1
        else:
            failed += 1
        
        time.sleep(0.3)
    
    print()
    print("=" * 60)
    print(f"  ✅ Downloaded: {success}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📂 Total data files: {len(list(DATA_DIR.glob('*.json')))}")
    print("=" * 60)
    print()
    print("Next: Run 'python create_database.py' to rebuild the database.")


if __name__ == "__main__":
    main()
