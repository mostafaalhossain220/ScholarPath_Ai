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
    results = rank_opportunities(profile, rows)

    for r in results[:10]:
        o = r["opportunity"]
        print(
            f"{r['final_score']:.2f} sem={r['semantic']:.2f} kw={r['keyword']:.2f} "
            f"{r['eligibility']['overall']:<18} {o['title'][:45]} [{o['degree_level']}]"
        )

    top = results[0]
    print("\nWhy:", top["opportunity"]["title"])
    for reason in top["reasons"]:
        print(" -", reason)
    for req in top["eligibility"]["requirements"]:
        print("  *", req["requirement"], req["status"], "-", req["reason"])