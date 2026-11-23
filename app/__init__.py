import os
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY was not found in the .env file")
    app.config["SECRET_KEY"] = secret_key

    # Session cookie hardening
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Largest request body accepted (CV upload limit)
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "scholarpath.db")

    from . import db
    db.init_app(app)

    from .routes import auth, changes, cv, opportunities, profile, saved
    app.register_blueprint(auth.bp)
    app.register_blueprint(opportunities.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(saved.bp)
    app.register_blueprint(changes.bp)
    app.register_blueprint(cv.bp)

    # `flask check-sources` command (source monitoring / change detection)
    from .services import monitoring
    monitoring.init_app(app)

    # The matching page needs the heavy 'sentence-transformers' package. If it is not
    # installed (e.g. small free hosting) skip that page instead of crashing the whole app.
    try:
        from .routes import matching
        app.register_blueprint(matching.bp)
        app.jinja_env.globals["matching_enabled"] = True
    except ImportError as error:
        app.logger.warning("Matching page disabled: %s", error)
        app.jinja_env.globals["matching_enabled"] = False

    # Lets templates write {{ csrf_token() }} inside forms
    app.jinja_env.globals["csrf_token"] = auth.get_csrf_token

    # {{ o.deadline|days_left }} -> days from today, or None if missing/invalid
    from datetime import date
    from .services.dashboard import days_until
    app.jinja_env.filters["days_left"] = lambda deadline: days_until(deadline, date.today())

    # {{ listing_countries() }} -> country names used in the listings (for pickers)
    from .services.countries import listing_countries
    app.jinja_env.globals["listing_countries"] = listing_countries

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Server"] = "ScholarPath-Gateway"
        # Prevent browser disk caching on dynamic authenticated pages to avoid DevTools cache leaks
        if request.endpoint and not request.endpoint.startswith("static"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.errorhandler(400)
    def bad_request(e):
        msg = getattr(e, "description", "Invalid or malformed request.")
        return render_template("errors.html", error_title="Bad Request (400)", error_message=str(msg)), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors.html", error_title="Access Forbidden (403)", error_message="You do not have permission to access this resource."), 403

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors.html", error_title="File Too Large (413)", error_message="The uploaded file is larger than 4 MB. Please upload a smaller CV."), 413

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors.html", error_title="Page Not Found (404)", error_message="The page you requested could not be found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors.html", error_title="Server Error (500)", error_message="An internal error occurred. Please try again later."), 500

    @app.route("/")
    def index():
        from flask import g
        from .db import get_db
        from .services.dashboard import build_dashboard

        dashboard = None
        if g.user:
            dashboard = build_dashboard(get_db(), g.user["id"])
        return render_template("index.html", dashboard=dashboard)

    return app
