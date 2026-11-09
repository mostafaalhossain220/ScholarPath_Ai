from flask import Blueprint, render_template

from app.db import get_db

bp = Blueprint("opportunities", __name__, url_prefix="/opportunities")


@bp.route("/")
def list_opportunities():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, title, provider, type, degree_level, country, funding, deadline
        FROM opportunities
        ORDER BY deadline IS NULL, deadline ASC
        """
    ).fetchall()
    return render_template("opportunities/list.html", opportunities=rows)