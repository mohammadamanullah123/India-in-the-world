import json
import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COUNTRIES_FILE = BASE_DIR / "countries.json"

_default_repo_db = BASE_DIR.parent / "src" / "data" / "dataoftheworld.db"
DB_FILE = _default_repo_db if _default_repo_db.parent.exists() else BASE_DIR / "dataoftheworld.db"


def load_json(filepath: Path) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_valid_country_codes(countries: list[dict]) -> set[str]:
    return {c["country_code"] for c in countries}


def create_countries_table(conn: sqlite3.Connection, countries: list[dict]):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            country_code TEXT PRIMARY KEY,
            country_name TEXT NOT NULL,
            flag TEXT,
            continent TEXT
        )
    """)
    conn.executemany(
        "INSERT OR REPLACE INTO countries (country_code, country_name, flag, continent) VALUES (?, ?, ?, ?)",
        [(c["country_code"], c["country_name"], c["flag"], c["continent"]) for c in countries]
    )


def create_index_table(conn: sqlite3.Connection, table_name: str, data: list[dict], valid_codes: set[str]):
    filtered_data = [(d["country_code"], d["year"], d["value"])
                     for d in data if d["country_code"] in valid_codes]

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            country_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            value REAL,
            PRIMARY KEY (country_code, year),
            FOREIGN KEY (country_code) REFERENCES countries(country_code)
        )
    """)
    conn.executemany(
        f'INSERT OR REPLACE INTO "{table_name}" (country_code, year, value) VALUES (?, ?, ?)',
        filtered_data
    )
    conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_year" ON "{table_name}"(year)')
    conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_country" ON "{table_name}"(country_code)')


def create_all_data_view(conn: sqlite3.Connection, index_tables: list[str]):
    if not index_tables:
        return

    conn.execute("DROP VIEW IF EXISTS all_data")
    conn.execute("DROP TABLE IF EXISTS all_data")
    
    cols = ", ".join(f'"{t}" REAL' for t in index_tables)
    conn.execute(f"CREATE TABLE all_data (country_code TEXT, year INTEGER, {cols}, PRIMARY KEY(country_code, year))")
    
    conn.execute("CREATE TEMP TABLE base_years (country_code TEXT, year INTEGER, PRIMARY KEY(country_code, year))")
    for t in index_tables:
        conn.execute(f'INSERT OR IGNORE INTO base_years SELECT country_code, year FROM "{t}"')
    
    conn.execute("INSERT INTO all_data (country_code, year) SELECT country_code, year FROM base_years")
    
    for t in index_tables:
        conn.execute(f'''
            UPDATE all_data 
            SET "{t}" = (SELECT value FROM "{t}" WHERE "{t}".country_code = all_data.country_code AND "{t}".year = all_data.year)
            WHERE EXISTS (SELECT 1 FROM "{t}" WHERE "{t}".country_code = all_data.country_code AND "{t}".year = all_data.year)
        ''')
    
    conn.execute("DROP TABLE base_years")


def create_database():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DB_FILE.exists():
        DB_FILE.unlink()

    countries = load_json(COUNTRIES_FILE)
    valid_codes = get_valid_country_codes(countries)

    json_files = sorted(DATA_DIR.glob("*.json"))
    index_tables = []

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA synchronous=NORMAL")

        create_countries_table(conn, countries)

        for json_file in json_files:
            table_name = json_file.stem
            data = load_json(json_file)
            create_index_table(conn, table_name, data, valid_codes)
            index_tables.append(table_name)
            print(f"Created table: {table_name}")

        create_all_data_view(conn, index_tables)
        print("Created view: all_data")

        conn.execute("ANALYZE")
        conn.commit()

    print(f"\nDatabase created: {DB_FILE}")


if __name__ == "__main__":
    create_database()
