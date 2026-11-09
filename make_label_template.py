import csv
import os

from app import create_app
from app.db import get_db

PROFILES = "data/eval_profiles.csv"
LABELS = "data/relevance_labels.csv"

if os.path.exists(LABELS):
    raise SystemExit(f"{LABELS} already exists, not overwriting your labels.")

app = create_app()
with app.app_context():
    opportunities = get_db().execute(
        "SELECT id, title, provider, degree_level, country FROM opportunities ORDER BY id"
    ).fetchall()

with open(PROFILES, newline="", encoding="utf-8-sig") as f:
    profiles = list(csv.DictReader(f))

with open(LABELS, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["profile_id", "opportunity_id", "opportunity", "relevant"])
    for p in profiles:
        for o in opportunities:
            name = f"{o['title']} | {o['provider']} | {o['degree_level']} | {o['country']}"
            writer.writerow([p["profile_id"], o["id"], name, ""])

print(f"Created {LABELS} with {len(profiles) * len(opportunities)} rows to label.")