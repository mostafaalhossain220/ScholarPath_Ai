import csv

from app import create_app
from app.db import get_db

PROFILES = "data/eval_profiles.csv"
LABELS = "data/relevance_labels.csv"

with open(PROFILES, newline="", encoding="utf-8-sig") as f:
    wanted = {r["profile_id"]: r["target_degree"] for r in csv.DictReader(f)}

app = create_app()
with app.app_context():
    degree = {
        str(r["id"]): r["degree_level"]
        for r in get_db().execute("SELECT id, degree_level FROM opportunities")
    }

with open(LABELS, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

auto_zero = 0
to_label = 0
for row in rows:
    if degree[row["opportunity_id"]] != wanted[row["profile_id"]]:
        row["relevant"] = "0"   # rule: degree does not match
        auto_zero += 1
    else:
        row["relevant"] = ""    # to be judged by a human
        to_label += 1

with open(LABELS, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Set to 0 by the degree rule: {auto_zero}. Left to label by hand: {to_label}.")