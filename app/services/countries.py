"""Country names that appear in the opportunity listings.

Used to suggest countries in the profile / matching / filter pickers, so a
student picks the same spelling the listings use (for example "UK", "USA").
"""
import re

from app.db import get_db


def split_countries(text):
    """'Belgium; Spain (confirm partners)' -> ['Belgium', 'Spain']"""
    without_notes = re.sub(r"\([^)]*\)", "", text or "")
    return [part.strip() for part in re.split(r"[;,]", without_notes) if part.strip()]


def listing_countries():
    """Distinct country names used by the opportunities table, sorted A-Z."""
    rows = get_db().execute(
        "SELECT DISTINCT country FROM opportunities WHERE country IS NOT NULL AND country != ''"
    ).fetchall()
    names = {}
    for row in rows:
        for name in split_countries(row["country"]):
            names.setdefault(name.lower(), name)
    return sorted(names.values(), key=str.lower)
