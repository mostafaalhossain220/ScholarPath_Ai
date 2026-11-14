import csv
import sys

from app import create_app
from app.db import get_db

PROFILES = "data/eval_profiles.csv"
LABELS = "data/relevance_labels.csv"


def load_rows():
    with open(LABELS, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def save_rows(fieldnames, rows):
    with open(LABELS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    wanted = sys.argv[1:]  # e.g. P01 P02 (empty means all profiles)

    with open(PROFILES, newline="", encoding="utf-8-sig") as f:
        profiles = {r["profile_id"]: r for r in csv.DictReader(f)}

    fieldnames, rows = load_rows()
    app = create_app()
    with app.app_context():
        opportunities = {
            str(r["id"]): r for r in get_db().execute("SELECT * FROM opportunities")
        }

    last_profile = None
    done = 0
    for row in rows:
        pid = row["profile_id"]
        if wanted and pid not in wanted:
            continue
        if row["relevant"].strip() in ("0", "1"):
            continue

        if pid != last_profile:
            p = profiles[pid]
            print("\n" + "=" * 72)
            print(f"PROFILE {pid}: wants {p['target_degree']} | field: {p['field']}")
            print(f"Preferred countries: {p['preferred_countries']}")
            print(f"Interests: {p['research_interests']} | Skills: {p['skills']}")
            print("=" * 72)
            last_profile = pid

        o = opportunities[row["opportunity_id"]]
        print(f"\n[{o['id']}] {o['title']}")
        print(f"   {o['provider']} | {o['degree_level']} | {o['country']} | field: {o['field'] or '-'}")
        print(f"   {(o['description'] or '')[:220]}")

        while True:
            answer = input("Relevant? 1=yes 0=no s=skip q=quit > ").strip().lower()
            if answer in ("1", "0", "s", "q"):
                break
        if answer == "q":
            break
        if answer == "s":
            continue

        row["relevant"] = answer
        save_rows(fieldnames, rows)  # saved after every answer, so you can stop any time
        done += 1

    labelled = sum(1 for r in rows if r["relevant"].strip() in ("0", "1"))
    print(f"\nLabelled this session: {done}. Total labelled: {labelled} of {len(rows)}.")


if __name__ == "__main__":
    main()