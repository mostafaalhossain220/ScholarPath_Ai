import sqlite3

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.db import get_db
from app.routes.auth import check_csrf, login_required

bp = Blueprint("saved", __name__, url_prefix="/saved")

STATUSES = ("saved", "preparing", "applied", "dropped")
NOTE_LIMIT = 500


@bp.route("/")
@login_required
def tracker():
    status = request.args.get("status", "").strip()
    db = get_db()

    conditions = ["s.user_id = ?"]
    params = [g.user["id"]]
    if status in STATUSES:
        conditions.append("s.status = ?")
        params.append(status)

    rows = db.execute(
        f"""
        SELECT s.id, s.status, s.note, o.id AS opportunity_id, o.title, o.provider,
               o.degree_level, o.country, o.deadline
        FROM saved_opportunities s
        JOIN opportunities o ON o.id = s.opportunity_id
        WHERE {" AND ".join(conditions)}
        ORDER BY o.deadline IS NULL, o.deadline ASC
        """,
        params,
    ).fetchall()

    counts = {s: 0 for s in STATUSES}
    for row in db.execute(
        "SELECT status, COUNT(*) AS total FROM saved_opportunities "
        "WHERE user_id = ? GROUP BY status", (g.user["id"],)
    ):
        counts[row["status"]] = row["total"]

    return render_template(
        "saved/tracker.html", items=rows, statuses=STATUSES,
        counts=counts, current=status if status in STATUSES else "",
    )


@bp.route("/add/<int:opportunity_id>", methods=("POST",))
@login_required
def add(opportunity_id):
    check_csrf()
    db = get_db()
    if db.execute("SELECT 1 FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone() is None:
        abort(404)
    try:
        db.execute(
            "INSERT INTO saved_opportunities (user_id, opportunity_id) VALUES (?, ?)",
            (g.user["id"], opportunity_id),
        )
        db.commit()
        flash("Saved to your tracker.", "success")
    except sqlite3.IntegrityError:
        flash("You have already saved this opportunity.", "info")
    return redirect(url_for("opportunities.detail", opportunity_id=opportunity_id))


def get_own_saved_or_404(saved_id):
    """Fetch a saved row only if it belongs to the logged-in user."""
    row = get_db().execute(
        "SELECT id FROM saved_opportunities WHERE id = ? AND user_id = ?",
        (saved_id, g.user["id"]),
    ).fetchone()
    if row is None:
        abort(404)


@bp.route("/<int:saved_id>/update", methods=("POST",))
@login_required
def update(saved_id):
    check_csrf()
    get_own_saved_or_404(saved_id)
    status = request.form.get("status", "")
    note = request.form.get("note", "").strip()

    if status not in STATUSES:
        flash("Invalid status.", "danger")
    elif len(note) > NOTE_LIMIT:
        flash(f"Note must be {NOTE_LIMIT} characters or fewer.", "danger")
    else:
        db = get_db()
        db.execute(
            "UPDATE saved_opportunities SET status = ?, note = ? WHERE id = ? AND user_id = ?",
            (status, note or None, saved_id, g.user["id"]),
        )
        db.commit()
        flash("Updated.", "success")
    return redirect(url_for("saved.tracker"))


@bp.route("/<int:saved_id>/remove", methods=("POST",))
@login_required
def remove(saved_id):
    check_csrf()
    get_own_saved_or_404(saved_id)
    db = get_db()
    db.execute("DELETE FROM saved_opportunities WHERE id = ? AND user_id = ?",
               (saved_id, g.user["id"]))
    db.commit()
    flash("Removed from your tracker.", "info")
    return redirect(url_for("saved.tracker"))
