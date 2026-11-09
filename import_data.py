import csv
from datetime import datetime

from app import create_app
from app.db import get_db

CSV_PATH = "data/opportunities.csv"
ALLOWED_TYPES = {"scholarship", "phd", "masters", "admission_and_scholarship"}
ALLOWED_DEGREES = {"masters", "phd"}
REQUIRED_COLUMNS = [
    "title", "provider", "type", "degree_level", "field", "country", "funding",
    "min_cgpa", "min_ielts", "deadline", "description", "requirements_text",
    "source_url", "last_checked",
]


def clean(value):
    """Strip spaces; return None for empty text."""
    value = (value or "").strip()
    return value or None


def to_float(value, label):
    """Convert a number column; empty means 'not provided' (None)."""
    value = clean(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{label} '{value}' is not a number")


def to_iso_date(value, label):
    """Accept YYYY-MM-DD or MM/DD/YYYY and return YYYY-MM-DD."""
    value = clean(value)
    if value is None:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"{label} '{value}' must look like YYYY-MM-DD or MM/DD/YYYY")


def build_records(raw):
    """Turn one CSV row into one or more database records.

    A row such as degree_level 'masters; phd' becomes two records,
    one per degree level, so filtering by degree level works.
    """
    title = clean(raw["title"])
    provider = clean(raw["provider"])
    source_url = clean(raw["source_url"])
    if not (title and provider and source_url):
        raise ValueError("title, provider and source_url are required")

    opp_type = clean(raw["type"])
    if opp_type not in ALLOWED_TYPES:
        raise ValueError(f"unknown type '{opp_type}'")

    degrees = [d.strip() for d in (raw["degree_level"] or "").split(";") if d.strip()]
    if not degrees or any(d not in ALLOWED_DEGREES for d in degrees):
        raise ValueError(f"unknown degree_level '{raw['degree_level']}'")

    deadline = to_iso_date(raw["deadline"], "deadline")
    last_checked = to_iso_date(raw["last_checked"], "last_checked")
    min_cgpa = to_float(raw["min_cgpa"], "min_cgpa")
    min_ielts = to_float(raw["min_ielts"], "min_ielts")

    return [
        (
            title, provider, opp_type, degree, clean(raw["field"]),
            clean(raw["country"]), clean(raw["funding"]), min_cgpa, min_ielts,
            deadline, clean(raw["description"]), clean(raw["requirements_text"]),
            source_url, last_checked,
        )
        for degree in degrees
    ]


INSERT_SQL = """
    INSERT INTO opportunities
    (title, provider, type, degree_level, field, country, funding,
     min_cgpa, min_ielts, deadline, description, requirements_text,
     source_url, last_checked)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_SQL = """
    UPDATE opportunities SET
        title=?, provider=?, type=?, degree_level=?, field=?, country=?,
        funding=?, min_cgpa=?, min_ielts=?, deadline=?, description=?,
        requirements_text=?, source_url=?, last_checked=?
    WHERE id=?
"""


def import_csv(path=CSV_PATH):
    app = create_app()
    inserted = updated = 0
    errors = []

    with app.app_context():
        db = get_db()
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                print("Missing columns in CSV:", ", ".join(missing))
                return

            for line_no, raw in enumerate(reader, start=2):
                try:
                    records = build_records(raw)
                except ValueError as error:
                    errors.append(f"line {line_no}: {error}")
                    continue

                for record in records:
                    existing = db.execute(
                        "SELECT id FROM opportunities "
                        "WHERE title = ? AND provider = ? AND degree_level = ?",
                        (record[0], record[1], record[3]),
                    ).fetchone()
                    if existing:
                        db.execute(UPDATE_SQL, record + (existing["id"],))
                        updated += 1
                    else:
                        db.execute(INSERT_SQL, record)
                        inserted += 1
        db.commit()

    print(f"Inserted: {inserted}, updated: {updated}, skipped rows: {len(errors)}")
    for message in errors:
        print("  skipped ->", message)


if __name__ == "__main__":
    import_csv()