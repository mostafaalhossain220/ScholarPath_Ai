from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.db import get_db
from app.routes.auth import check_csrf, login_required

bp = Blueprint("profile", __name__, url_prefix="/profile")

TEXT_LIMITS = {
    "field": 100,
    "preferred_countries": 200,
    "research_interests": 500,
    "skills": 500,
}
FUNDING_CHOICES = {
    "full": "Full funding only",
    "partial": "Partial or full funding",
    "none": "Funding not needed",
}
FORM_FIELDS = [
    "cgpa", "ielts", "target_degree", "field", "preferred_countries",
    "research_interests", "skills", "funding_need",
]


def parse_number(value, label, low, high):
    """Return (number or None, error or None). Empty text means 'not provided'."""
    if value == "":
        return None, None
    try:
        number = float(value)
    except ValueError:
        return None, f"{label} must be a number."
    if not low <= number <= high:
        return None, f"{label} must be between {low:g} and {high:g}."
    return number, None


def validate_profile(form):
    """Return (clean_values, errors). `form` is a dict of stripped strings."""
    clean, errors = {}, {}

    clean["cgpa"], error = parse_number(form["cgpa"], "CGPA", 0, 4)
    if error:
        errors["cgpa"] = error

    clean["ielts"], error = parse_number(form["ielts"], "IELTS", 0, 9)
    if error:
        errors["ielts"] = error

    if form["target_degree"] not in ("", "masters", "phd"):
        errors["target_degree"] = "Choose Master's or PhD."
    clean["target_degree"] = form["target_degree"] or None

    for name, limit in TEXT_LIMITS.items():
        if len(form[name]) > limit:
            errors[name] = f"Please keep this under {limit} characters."
        clean[name] = form[name] or None

    if form["funding_need"] not in ("", *FUNDING_CHOICES):
        errors["funding_need"] = "Choose one of the listed options."
    clean["funding_need"] = form["funding_need"] or None
    return clean, errors


def empty_form():
    return {name: "" for name in FORM_FIELDS}


@bp.route("/", methods=("GET", "POST"))
@login_required
def edit():
    db = get_db()
    errors = {}

    if request.method == "POST":
        check_csrf()
        form = {name: request.form.get(name, "").strip() for name in FORM_FIELDS}
        clean, errors = validate_profile(form)

        if not errors:
            db.execute(
                """
                INSERT INTO profiles
                    (user_id, cgpa, ielts, target_degree, field, preferred_countries,
                     research_interests, skills, funding_need, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    cgpa = excluded.cgpa, ielts = excluded.ielts,
                    target_degree = excluded.target_degree, field = excluded.field,
                    preferred_countries = excluded.preferred_countries,
                    research_interests = excluded.research_interests,
                    skills = excluded.skills, funding_need = excluded.funding_need,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (g.user["id"], clean["cgpa"], clean["ielts"], clean["target_degree"],
                 clean["field"], clean["preferred_countries"], clean["research_interests"],
                 clean["skills"], clean["funding_need"]),
            )
            db.commit()
            flash("Profile saved.", "success")
            return redirect(url_for("profile.edit"))
    else:
        form = empty_form()
        row = db.execute("SELECT * FROM profiles WHERE user_id = ?", (g.user["id"],)).fetchone()
        if row:
            form = {name: "" if row[name] is None else str(row[name]) for name in FORM_FIELDS}

    return render_template(
        "profile/edit.html", form=form, errors=errors, funding_choices=FUNDING_CHOICES
    )
