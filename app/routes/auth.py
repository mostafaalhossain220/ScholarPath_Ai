import re
import secrets
import sqlite3
from functools import wraps

from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


# ---------- helpers ----------

def get_csrf_token():
    """Return this session's CSRF token (create it once)."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def check_csrf():
    """Stop any POST that does not carry the session's CSRF token."""
    sent = request.form.get("csrf_token", "")
    if not sent or not secrets.compare_digest(sent, session.get("csrf_token", "")):
        abort(400, "Invalid or missing form token. Please reload the page and try again.")


def login_required(view):
    """Decorator for pages that need a logged-in user."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def validate_registration(name, email, password, confirm):
    """Return a dict of field -> error message. Empty dict means valid."""
    errors = {}
    if not name:
        errors["name"] = "Name is required."
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or fewer."

    if not email:
        errors["email"] = "Email is required."
    elif len(email) > 254 or not EMAIL_PATTERN.match(email):
        errors["email"] = "Enter a valid email address."

    if len(password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    elif not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
        errors["password"] = "Password must contain at least one letter and one number."
    elif len(password) > 128:
        errors["password"] = "Password must be 128 characters or fewer."

    if "password" not in errors and password != confirm:
        errors["confirm"] = "Passwords do not match."
    return errors


# ---------- load current user on every request ----------

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()


# ---------- routes ----------

@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user:
        return redirect(url_for("index"))

    form = {"name": "", "email": ""}
    errors = {}

    if request.method == "POST":
        check_csrf()
        form["name"] = request.form.get("name", "").strip()
        form["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        errors = validate_registration(form["name"], form["email"], password, confirm)

        if not errors:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (form["name"], form["email"], generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                errors["email"] = "An account with this email already exists."
            else:
                flash("Account created. Please log in.", "success")
                return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, errors=errors)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        return redirect(url_for("index"))

    email = ""
    error = None
    next_page = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        check_csrf()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

        # Same message for "no such email" and "wrong password" so emails cannot be guessed.
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Incorrect email or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("index"))

    return render_template("auth/login.html", email=email, error=error, next=next_page)


@bp.route("/logout", methods=("POST",))
def logout():
    check_csrf()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
