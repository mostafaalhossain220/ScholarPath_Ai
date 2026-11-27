import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.db import get_db

app = create_app()
with app.app_context():
    rows = get_db().execute(
        "SELECT id, title, field, degree_level, country FROM opportunities ORDER BY id"
    ).fetchall()
    for r in rows:
        print(r["id"], "|", r["title"], "|", r["field"], "|", r["degree_level"], "|", r["country"])