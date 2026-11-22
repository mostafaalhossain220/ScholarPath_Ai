from app import create_app
from app.db import get_db
from app.services.ranking import rank_opportunities

profile = {
    "target_degree": "phd",
    "cgpa": 3.4,
    "ielts": None,
    "field": "Computer Science",
    "preferred_countries": "UK; USA",
    "research_interests": "natural language processing, machine translation",
    "skills": "Python, PyTorch",
}

app = create_app()
with app.app_context():
    rows = get_db().execute("SELECT * FROM opportunities").fetchall()
    results = rank_opportunities(profile, rows, with_evidence=True)

for r in results[:3]:
    o = r["opportunity"]
    print("\n==", r["final_score"].__round__(2), o["title"][:55], "|", o["provider"][:25])
    for req in r["eligibility"]["requirements"]:
        ev = req.get("evidence") or {}
        sentence = ev.get("sentence") or "(no supporting sentence found)"
        print(f"  {req['requirement']:13} {req['status']:13} | {sentence[:100]}")

print("\nEvidence attached to", sum(1 for r in results if r["evidence"]), "of", len(results), "results")