import csv
from collections import Counter

rows = list(csv.DictReader(open("data/evidence_review.csv", encoding="utf-8-sig")))
checked = [r for r in rows if r["verdict"].strip() in ("ok", "weak", "wrong")]
none = [r for r in rows if r["verdict"].strip() == "none"]
unchecked = [r for r in rows if not r["verdict"].strip()]

print(f"Total rows: {len(rows)} | checked: {len(checked)} | no sentence found: {len(none)} | not checked yet: {len(unchecked)}\n")

groups = [("ALL", checked)]
for m in ("keyword", "semantic"):
    groups.append((m, [r for r in checked if r["method"] == m]))
for q in sorted({r["requirement"] for r in checked}):
    groups.append((q, [r for r in checked if r["requirement"] == q]))

for scope, group in groups:
    if not group:
        continue
    c = Counter(r["verdict"] for r in group)
    n = len(group)
    print(f"{scope:13} n={n:3}  ok {c['ok']/n:5.0%}  weak {c['weak']/n:5.0%}  wrong {c['wrong']/n:5.0%}")
