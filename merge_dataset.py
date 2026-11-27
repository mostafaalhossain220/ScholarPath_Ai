import csv
from pathlib import Path

old_file = Path("data/opportunities.csv")
new_file = Path("data/new_opportunities.csv")
backup_file = Path("data/opportunities_backup.csv")

if not old_file.exists() or not new_file.exists():
    raise FileNotFoundError("CSV file missing. Check data folder.")

with old_file.open(encoding="utf-8-sig", newline="") as f:
    old_rows = list(csv.DictReader(f))
    columns = list(old_rows[0].keys()) if old_rows else None

if not columns:
    raise ValueError("Existing CSV has no data rows.")

with new_file.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames != columns:
        raise ValueError("CSV columns do not match!")
    new_rows = list(reader)

merged = old_rows.copy()
seen = {
    (r["title"].strip().lower(),
     r["provider"].strip().lower(),
     r["degree_level"].strip().lower())
    for r in merged
}

added = 0
for row in new_rows:
    key = (
        row["title"].strip().lower(),
        row["provider"].strip().lower(),
        row["degree_level"].strip().lower()
    )
    if key not in seen:
        merged.append(row)
        seen.add(key)
        added += 1

with old_file.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(merged)

print("Old CSV records:", len(old_rows))
print("New CSV records:", len(new_rows))
print("Added records:", added)
print("Final CSV records:", len(merged))
