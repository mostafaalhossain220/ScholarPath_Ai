from flask import Blueprint, render_template, request

from app.db import get_db

bp = Blueprint("opportunities", __name__, url_prefix="/opportunities")


@bp.route("/")
def list_opportunities():
    filters = {
        "q": request.args.get("q", "").strip(),
        "degree": request.args.get("degree", "").strip(),
        "country": request.args.get("country", "").strip(),
        "field": request.args.get("field", "").strip(),
        "deadline_before": request.args.get("deadline_before", "").strip(),
        "upcoming": request.args.get("upcoming", "").strip(),
    }

    conditions = []
    params = []

    # Keyword search: every word must appear in at least one of these columns
    for word in filters["q"].split():
        conditions.append(
            "(title LIKE ? OR provider LIKE ? OR description LIKE ? OR field LIKE ?)"
        )
        params.extend([f"%{word}%"] * 4)

    if filters["degree"] in ("masters", "phd"):
        conditions.append("degree_level = ?")
        params.append(filters["degree"])
    if filters["country"]:
        conditions.append("country LIKE ?")
        params.append(f"%{filters['country']}%")
    if filters["field"]:
        conditions.append("field LIKE ?")
        params.append(f"%{filters['field']}%")
    if filters["deadline_before"]:
        conditions.append("deadline <= ?")
        params.append(filters["deadline_before"])
    if filters["upcoming"] == "1":
        conditions.append("deadline >= date('now')")

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    db = get_db()
    rows = db.execute(
        f"""
        SELECT id, title, provider, type, degree_level, country, funding, deadline
        FROM opportunities
        {where}
        ORDER BY deadline IS NULL, deadline ASC
        """,
        params,
    ).fetchall()

    return render_template("opportunities/list.html", opportunities=rows, filters=filters)