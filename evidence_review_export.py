import csv
import os

from app import create_app
from app.db import get_db
from app.services.evidence import get_evidence

OUT = "data/evidence_review.csv"
if os.path.exists(OUT):
    raise SystemExit(f"{OUT} already exists, not overwriting your verdicts.")

app = create_app()
with app.app_context():
    rows = get_db().execute("SELECT * FROM opportunities ORDER BY id").fetchall()

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["opportunity_id", "title", "requirement", "method", "sentence", "verdict"])
    for row in rows:
        for name, ev in get_evidence(row).items():
            writer.writerow([
                row["id"], row["title"][:60], name,
                ev["method"] or "none", ev["sentence"] or "",
                "" if ev["sentence"] else "none",
            ])

print("Wrote", OUT)