import csv
from collections import Counter, defaultdict
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "evidence_review.csv"

with open(PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

verdicts = sorted({r["verdict"] for r in rows})
print(f"Rows: {len(rows)}")
print(f"Verdict values found: {verdicts}\n")


def summarize(title, groups):
    print(title)
    header = f"{'group':<18}{'n':>5}{'ok':>7}{'weak':>7}{'other':>7}{'strict':>9}{'lenient':>9}"
    print(header)
    for name, items in sorted(groups.items()):
        c = Counter(r["verdict"] for r in items)
        n = len(items)
        ok, weak = c.get("ok", 0), c.get("weak", 0)
        other = n - ok - weak
        print(f"{name:<18}{n:>5}{ok:>7}{weak:>7}{other:>7}{ok / n:>9.3f}{(ok + weak) / n:>9.3f}")
    print()


by_method = defaultdict(list)
by_req = defaultdict(list)
for r in rows:
    by_method[r["method"]].append(r)
    by_req[r["requirement"]].append(r)

summarize("By method", by_method)
summarize("By requirement", by_req)
summarize("Overall", {"all": rows})

print("strict  = ok / total            (evidence correctness)")
print("lenient = (ok + weak) / total")
print("unsupported-evidence rate (strict) = 1 - strict")