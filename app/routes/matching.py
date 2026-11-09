from flask import Blueprint, g, render_template, request

from app.db import get_db
from app.routes.auth import login_required
from app.services.ranking import rank_opportunities

bp = Blueprint("matching", __name__, url_prefix="/matching")

FORM_FIELDS = [
    "target_degree", "cgpa", "ielts", "field",
    "preferred_countries", "research_interests", "skills",
]


def parse_number(value, low, high, label):
    """Return (number or None, error message or None). Empty means 'not provided'."""
    value = (value or "").strip()
    if not value:
        return None, None
    try:
        number = float(value)
    except ValueError:
        return None, f"{label} must be a number."
    if not low <= number <= high:
        return None, f"{label} must be between {low} and {high}."
    return number, None


@bp.route("/", methods=["GET", "POST"])
@login_required
def match():
    form = {name: "" for name in FORM_FIELDS}
    errors = []
    results = None

    if request.method == "GET" and g.user:
        db = get_db()
        db_profile = db.execute(
            "SELECT * FROM profiles WHERE user_id = ?", (g.user["id"],)
        ).fetchone()
        if db_profile:
            for field in FORM_FIELDS:
                val = db_profile[field]
                form[field] = "" if val is None else str(val)

    if request.method == "POST":
        form = {name: request.form.get(name, "").strip() for name in FORM_FIELDS}

        cgpa, error = parse_number(form["cgpa"], 0, 4, "CGPA (on a 4.0 scale)")
        if error:
            errors.append(error)
        ielts, error = parse_number(form["ielts"], 0, 9, "IELTS")
        if error:
            errors.append(error)
        if form["target_degree"] not in ("", "masters", "phd"):
            errors.append("Choose a valid degree level.")
        if not form["research_interests"] and not form["field"]:
            errors.append("Enter your field or research interests so we can compare them.")

        if not errors:
            profile = {
                "target_degree": form["target_degree"] or None,
                "cgpa": cgpa,
                "ielts": ielts,
                "field": form["field"],
                "preferred_countries": form["preferred_countries"],
                "research_interests": form["research_interests"],
                "skills": form["skills"],
            }
            rows = get_db().execute("SELECT * FROM opportunities").fetchall()
            results = rank_opportunities(profile, rows)

    return render_template("matching/match.html", form=form, errors=errors, results=results)