import csv
import datetime
import os
import sys

PATH = "data/evidence_review.csv"
LOG = "data/evidence_review_changes.csv"

if len(sys.argv) != 4 or sys.argv[3] not in ("ok", "weak", "wrong"):
    raise SystemExit('Usage: python evidence_review_fix.py <opportunity_id> "<requirement>" <ok|weak|wrong>')

opp_id, requirement, new = sys.argv[1], sys.argv[2], sys.argv[3]

with open(PATH, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

matches = [r for r in rows if r["opportunity_id"] == opp_id and r["requirement"] == requirement]
if len(matches) != 1:
    raise SystemExit(f"Found {len(matches)} matching rows, expected exactly 1.")

row = matches[0]
print("Title:   ", row["title"])
print("Sentence:", row["sentence"])
print("Current verdict:", row["verdict"], "-> new:", new)
reason = input("Why does the old verdict not fit the definition? > ").strip()
if not reason:
    raise SystemExit("A reason is required. Nothing changed.")

old = row["verdict"]
row["verdict"] = new

with open(PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

write_header = not os.path.exists(LOG)
with open(LOG, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if write_header:
        writer.writerow(["date", "opportunity_id", "requirement", "old", "new", "reason"])
    writer.writerow([datetime.date.today().isoformat(), opp_id, requirement, old, new, reason])

print("Saved and logged.")
