import csv
from pathlib import Path

RELEVANT = {
    "P01": {2, 3, 4, 5, 6, 8, 9, 10, 12, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 50},
    "P02": {2, 4, 5, 6, 9, 10, 12, 21, 24, 30, 50},
    "P03": {7, 11, 13, 14, 31, 33, 34, 35, 38, 39, 40, 41, 45, 46},
    "P04": {22},
    "P05": {32},
}

out = Path(__file__).resolve().parent / "labels.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["profile_id", "opportunity_id", "relevant"])
    for pid, rel in RELEVANT.items():
        for oid in range(1, 51):
            w.writerow([pid, oid, 1 if oid in rel else 0])
print("labels.csv written")