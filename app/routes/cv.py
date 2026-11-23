from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.db import get_db
from app.routes.auth import check_csrf, login_required
from app.routes.profile import FORM_FIELDS, FUNDING_CHOICES, empty_form, validate_profile
from app.services.cv_matching import rank_for_profile
from app.services.cv_parser import CVError, extract_text, parse_cv

bp = Blueprint("cv", __name__, url_prefix="/cv")

TOP_N = 10
FIELD_LABELS = {
    "cgpa": "CGPA", "ielts": "IELTS", "target_degree": "Target degree", "field": "Field of study",
    "research_interests": "Research interests", "skills": "Skills",
}


def _saved_profile(db, user_id):
    row = db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        return empty_form()
    return {name: "" if row[name] is None else str(row[name]) for name in FORM_FIELDS}


@bp.route("/", methods=("GET", "POST"))
@login_required
def upload():
    """Step 1: upload a CV. Step 2 (same page): review what we found."""
    if request.method == "GET":
        return render_template("cv/upload.html", review=None)

    check_csrf()
    file = request.files.get("cv")
    if file is None or not file.filename:
        flash("Please choose a CV file first.", "warning")
        return redirect(url_for("cv.upload"))
    try:
        text = extract_text(file.filename, file.read())
    except CVError as error:
        flash(str(error), "danger")
        return redirect(url_for("cv.upload"))

    result = parse_cv(text)
    # Start from the saved profile; CV values replace it only where something was found.
    form = _saved_profile(get_db(), g.user["id"])
    for key in result["found"]:
        form[key] = result["values"][key]

    review = {"form": form, "found": result["found"], "notes": result["notes"],
              "filename": file.filename, "labels": FIELD_LABELS}
    return render_template("cv/upload.html", review=review, errors={},
                           funding_choices=FUNDING_CHOICES)


@bp.route("/apply", methods=("POST",))
@login_required
def apply():
    """Step 3: save the reviewed values to the profile and show matches."""
    check_csrf()
    form = {name: request.form.get(name, "").strip() for name in FORM_FIELDS}
    clean, errors = validate_profile(form)
    if errors:
        review = {"form": form, "found": [], "notes": [], "filename": None, "labels": FIELD_LABELS}
        return render_template("cv/upload.html", review=review, errors=errors,
                               funding_choices=FUNDING_CHOICES), 400

    db = get_db()
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
        (g.user["id"], clean["cgpa"], clean["ielts"], clean["target_degree"], clean["field"],
         clean["preferred_countries"], clean["research_interests"], clean["skills"],
         clean["funding_need"]),
    )
    db.commit()
    flash("Profile updated from your CV.", "success")
    return redirect(url_for("cv.matches"))


@bp.route("/matches")
@login_required
def matches():
    """Opportunities ranked for the saved profile."""
    db = get_db()
    profile = db.execute("SELECT * FROM profiles WHERE user_id = ?", (g.user["id"],)).fetchone()
    if profile is None:
        flash("Upload your CV first so we can build your profile.", "warning")
        return redirect(url_for("cv.upload"))

    degree = profile["target_degree"]
    if degree in ("masters", "phd"):
        rows = db.execute("SELECT * FROM opportunities WHERE degree_level = ?", (degree,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM opportunities").fetchall()

    results, method = rank_for_profile(profile, rows)
    show_all = request.args.get("all") == "1"
    shown = results if show_all else results[:TOP_N]
    return render_template("cv/matches.html", results=shown, total=len(results), method=method,
                           profile=profile, show_all=show_all)
