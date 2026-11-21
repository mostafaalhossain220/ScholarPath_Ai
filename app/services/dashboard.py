"""Data for the student dashboard.

Everything here reads tables that already exist (profiles, opportunities,
saved_opportunities) and reuses the rule-based eligibility check, so the
dashboard works even when the optional sentence-transformers package is missing.
"""
from datetime import date

from app.services.eligibility import check_eligibility

# Profile fields shown in the completeness meter, with friendly labels.
PROFILE_FIELDS = {
    "target_degree": "Target degree",
    "field": "Field of study",
    "cgpa": "CGPA",
    "ielts": "IELTS score",
    "preferred_countries": "Preferred countries",
    "funding_need": "Funding need",
    "skills": "Skills",
    "research_interests": "Research interests",
}

# How many days ahead counts as an "approaching" deadline.
DEADLINE_WINDOW_DAYS = 60
TOP_PICKS_LIMIT = 3
DEADLINES_LIMIT = 5


def profile_completeness(profile):
    """Return (percent, missing_labels) for a profile row (or None)."""
    missing = []
    for key, label in PROFILE_FIELDS.items():
        value = profile[key] if profile is not None else None
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(label)
    filled = len(PROFILE_FIELDS) - len(missing)
    return round(filled * 100 / len(PROFILE_FIELDS)), missing


def days_until(deadline, today):
    """Days from today to an ISO date string, or None if missing/invalid."""
    if not deadline:
        return None
    try:
        return (date.fromisoformat(deadline) - today).days
    except ValueError:
        return None


def build_dashboard(db, user_id, today=None):
    """Collect everything the dashboard template needs for one user."""
    today = today or date.today()

    profile = db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    percent, missing = profile_completeness(profile)

    saved_rows = db.execute(
        """
        SELECT s.status, o.id AS opportunity_id, o.title, o.provider, o.degree_level,
               o.country, o.deadline
        FROM saved_opportunities s
        JOIN opportunities o ON o.id = s.opportunity_id
        WHERE s.user_id = ?
        """,
        (user_id,),
    ).fetchall()

    status_counts = {"saved": 0, "preparing": 0, "applied": 0, "dropped": 0}
    for row in saved_rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    # Approaching deadlines among the student's own tracked (not dropped) items.
    deadlines = []
    for row in saved_rows:
        if row["status"] == "dropped":
            continue
        left = days_until(row["deadline"], today)
        if left is not None and 0 <= left <= DEADLINE_WINDOW_DAYS:
            deadlines.append({**dict(row), "days_left": left})
    deadlines.sort(key=lambda item: item["days_left"])

    opportunities = db.execute("SELECT * FROM opportunities").fetchall()
    open_opportunities = [
        o for o in opportunities
        if days_until(o["deadline"], today) is None or days_until(o["deadline"], today) >= 0
    ]

    # Rule-based eligibility (degree, CGPA, IELTS). Only meaningful with a profile.
    eligible_count = None
    top_picks = []
    if profile is not None:
        saved_ids = {row["opportunity_id"] for row in saved_rows}
        scored = []
        for o in open_opportunities:
            result = check_eligibility(profile, o)
            if result["overall"] == "not_satisfied":
                continue
            scored.append({
                "id": o["id"],
                "title": o["title"],
                "provider": o["provider"],
                "degree_level": o["degree_level"],
                "country": o["country"],
                "deadline": o["deadline"],
                "days_left": days_until(o["deadline"], today),
                "overall": result["overall"],
                "is_saved": o["id"] in saved_ids,
            })
        eligible_count = len(scored)
        # Fully satisfied first, then the closest deadline (unknown deadlines last).
        scored.sort(key=lambda item: (
            item["overall"] != "satisfied",
            item["days_left"] is None,
            item["days_left"] if item["days_left"] is not None else 0,
        ))
        top_picks = scored[:TOP_PICKS_LIMIT]

    return {
        "has_profile": profile is not None,
        "completeness": percent,
        "missing_fields": missing,
        "saved_total": sum(v for k, v in status_counts.items() if k != "dropped"),
        "status_counts": status_counts,
        "open_total": len(open_opportunities),
        "eligible_count": eligible_count,
        "deadlines": deadlines[:DEADLINES_LIMIT],
        "top_picks": top_picks,
    }
