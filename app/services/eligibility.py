def _to_float(value):
    """Convert a value to float, or return None if it is missing or invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check_minimum(label, user_value, required_value):
    """Compare a student's score with a minimum requirement (CGPA, IELTS)."""
    required = _to_float(required_value)
    user = _to_float(user_value)

    if required is None:
        return {
            "requirement": label,
            "status": "not_provided",
            "reason": f"The opportunity does not state a minimum {label}.",
        }
    if user is None:
        return {
            "requirement": label,
            "status": "unclear",
            "reason": f"Add your {label} to your profile to check this requirement.",
        }
    if user >= required:
        return {
            "requirement": label,
            "status": "satisfied",
            "reason": f"Your {label} ({user}) meets the minimum ({required}).",
        }
    return {
        "requirement": label,
        "status": "not_satisfied",
        "reason": f"Your {label} ({user}) is below the minimum ({required}).",
    }


def _check_degree(profile_degree, opportunity_degree):
    """Check that the degree level the student wants matches the opportunity."""
    if not opportunity_degree:
        return {
            "requirement": "degree level",
            "status": "not_provided",
            "reason": "The opportunity does not state a degree level.",
        }
    if not profile_degree:
        return {
            "requirement": "degree level",
            "status": "unclear",
            "reason": "Add your target degree level to your profile.",
        }
    if profile_degree.strip().lower() == opportunity_degree.strip().lower():
        return {
            "requirement": "degree level",
            "status": "satisfied",
            "reason": f"This is a {opportunity_degree} opportunity, as you are looking for.",
        }
    return {
        "requirement": "degree level",
        "status": "not_satisfied",
        "reason": f"This is a {opportunity_degree} opportunity, but you are looking for {profile_degree}.",
    }


def check_eligibility(profile, opportunity):
    """Return requirement-by-requirement results and an overall status.

    profile and opportunity are dictionaries (or sqlite3.Row objects).
    The result is advisory: users must confirm details on the official source.
    """
    results = [
        _check_degree(profile["target_degree"], opportunity["degree_level"]),
        _check_minimum("CGPA", profile["cgpa"], opportunity["min_cgpa"]),
        _check_minimum("IELTS", profile["ielts"], opportunity["min_ielts"]),
    ]

    statuses = [r["status"] for r in results]
    if "not_satisfied" in statuses:
        overall = "not_satisfied"
    elif "unclear" in statuses or "not_provided" in statuses:
        overall = "needs_verification"
    else:
        overall = "satisfied"

    return {"overall": overall, "requirements": results}