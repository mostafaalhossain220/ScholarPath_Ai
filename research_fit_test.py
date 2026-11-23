from app import create_app
from app.db import get_db
from app.services.research_fit import get_research_fit

profile = {
    "research_interests": "natural language processing, machine translation",
    "field": "Computer Science",
    "skills": "Python, PyTorch",
}

app = create_app()
with app.app_context():
    rows = get_db().execute("SELECT * FROM opportunities WHERE degree_level = 'phd'").fetchall()

results = []
for row in rows:
    fit = get_research_fit(profile, row)
    if fit:
        results.append((fit["score"], row, fit))

for score, row, fit in sorted(results, key=lambda x: -x[0]):
    best = fit["matches"][0]["sentence"][:90] if fit["matches"] else "-"
    print(f"{score:.2f} {fit['label']:8} {row['title'][:42]:42} | words: {', '.join(fit['shared_terms'][:4]) or '-'}")
    print(f"      best: {best}")