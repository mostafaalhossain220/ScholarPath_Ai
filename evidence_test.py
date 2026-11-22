from app import create_app
from app.db import get_db
from app.services.evidence import get_evidence

app = create_app()
with app.app_context():
    rows = get_db().execute("SELECT * FROM opportunities ORDER BY id").fetchall()

found = {"keyword": 0, "semantic": 0, "none": 0}
for row in rows:
    for name, ev in get_evidence(row).items():
        found[ev["method"] or "none"] += 1

print("Evidence found over", len(rows), "opportunities x 4 requirements:", found)

for row in rows[:4]:
    print("\n==", row["title"][:60], "|", row["provider"][:30])
    for name, ev in get_evidence(row).items():
        text = ev["sentence"] or "(no supporting sentence found)"
        print(f"  {name:13} [{ev['method'] or '-'}] {text[:110]}")