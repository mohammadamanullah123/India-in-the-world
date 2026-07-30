import json, sys, io, sqlite3
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with open("src/data/indicators.json") as f:
    indicators = json.load(f)

ind_ids = {i["id"] for i in indicators}
print(f"Indicators in JSON: {len(indicators)}")

db = sqlite3.connect("src/data/dataoftheworld.db")
cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'countries'")
tables = [r[0] for r in cursor.fetchall()]
db.close()

table_set = set(tables)
print(f"Tables in database: {len(tables)}")

in_db_not_json = table_set - ind_ids
in_json_not_db = ind_ids - table_set

if in_db_not_json:
    print(f"\nIn DB but NOT in indicators.json ({len(in_db_not_json)}):")
    for t in sorted(in_db_not_json):
        print(f"  - {t}")

if in_json_not_db:
    print(f"\nIn indicators.json but NOT in DB ({len(in_json_not_db)}):")
    for t in sorted(in_json_not_db):
        print(f"  - {t}")

if not in_db_not_json and not in_json_not_db:
    print("\nPerfect match! All DB tables have indicator metadata.")

cats = {}
for i in indicators:
    cats.setdefault(i["category"], []).append(i["id"])
print(f"\nCategories:")
for cat, items in sorted(cats.items()):
    print(f"  {cat}: {len(items)} indicators")
