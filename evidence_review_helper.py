import csv

PATH = "data/evidence_review.csv"
CHOICES = {"1": "ok", "2": "weak", "3": "wrong"}

with open(PATH, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)


def save():
    with open(PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


todo = [r for r in rows if not r["verdict"].strip()]
print(f"{len(todo)} sentences to check. 1 = ok, 2 = weak, 3 = wrong, s = skip, q = quit")
print("ok = really about this requirement | weak = related but not clear | wrong = about something else")

done = 0
for r in todo:
    print("\n" + "-" * 70)
    print(f"{r['title']}")
    print(f"Requirement: {r['requirement'].upper()}")
    print(f"Sentence:    {r['sentence']}")
    while True:
        answer = input("Verdict? [1/2/3/s/q] > ").strip().lower()
        if answer in CHOICES or answer in ("s", "q"):
            break
    if answer == "q":
        break
    if answer == "s":
        continue
    r["verdict"] = CHOICES[answer]
    save()  # saved after every answer
    done += 1

left = sum(1 for r in rows if not r["verdict"].strip())
print(f"\nChecked this session: {done}. Still to check: {left}.")