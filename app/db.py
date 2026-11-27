
import sqlite3

import click
from flask import current_app, g


def get_db():
    """Open a database connection and reuse it during the request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def migrate_opportunities_type(db):
    """
    Update the opportunities table CHECK constraint to support
    the new 'admission' type without deleting existing records.
    """

    table = db.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'opportunities'
        """
    ).fetchone()

    # New database: no migration needed.
    if table is None:
        return

    # Check whether admission is already allowed.
    table_info = db.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = 'opportunities'
        """
    ).fetchone()

    if "'admission'" in (table_info["sql"] or ""):
        return

    print("Migrating opportunities table...")

    # Make sure no transaction is active before changing this setting.
    db.commit()
    db.execute("PRAGMA foreign_keys = OFF")

    try:
        db.execute("BEGIN IMMEDIATE")

        db.execute("DROP TABLE IF EXISTS opportunities_new")

        db.execute(
            """
            CREATE TABLE opportunities_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                provider TEXT NOT NULL,
                type TEXT NOT NULL CHECK (
                    type IN (
                        'scholarship',
                        'phd',
                        'masters',
                        'admission',
                        'admission_and_scholarship'
                    )
                ),
                degree_level TEXT NOT NULL
                    CHECK (degree_level IN ('masters', 'phd')),
                field TEXT,
                country TEXT,
                funding TEXT,
                min_cgpa REAL,
                min_ielts REAL,
                deadline TEXT,
                description TEXT,
                requirements_text TEXT,
                source_url TEXT NOT NULL,
                last_checked TEXT
            )
            """
        )

        # Copy all existing records, including their original IDs.
        db.execute(
            """
            INSERT INTO opportunities_new (
                id, title, provider, type, degree_level, field,
                country, funding, min_cgpa, min_ielts, deadline,
                description, requirements_text, source_url, last_checked
            )
            SELECT
                id, title, provider, type, degree_level, field,
                country, funding, min_cgpa, min_ielts, deadline,
                description, requirements_text, source_url, last_checked
            FROM opportunities
            """
        )

        # Replace the old table with the new table.
        db.execute("DROP TABLE opportunities")
        db.execute(
            "ALTER TABLE opportunities_new RENAME TO opportunities"
        )

        db.commit()
        print("Opportunities table migration successful.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.execute("PRAGMA foreign_keys = ON")


def init_db():
    """Run migration and initialize all database tables."""

    db = get_db()

    # First update the existing table if necessary.
    migrate_opportunities_type(db)

    # Then create any missing tables and indexes.
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))

    # Verify foreign key relationships.
    violations = db.execute("PRAGMA foreign_key_check").fetchall()

    if violations:
        raise RuntimeError(
            f"Database foreign key violations found: {violations}"
        )


@click.command("init-db")
def init_db_command():
    """Flask command: initialize and migrate database."""

    init_db()
    click.echo("Database initialized successfully.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
