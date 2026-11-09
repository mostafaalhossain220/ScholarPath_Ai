from app import create_app
from app.db import get_db
from app.services.semantic_matcher import semantic_scores

student = "natural language processing and machine translation"

app = create_app()
with app.app_context():
    rows = get_db().execute(
        "SELECT id, title, provider, field, description FROM opportunities"
    ).fetchall()
    scores = semantic_scores(student, rows)
    ranked = sorted(zip(scores, rows), key=lambda x: -x[0])
    for score, row in ranked[:8]:
        print(f"{score:.3f}  {row['title'][:60]}  ({row['provider'][:25]})")