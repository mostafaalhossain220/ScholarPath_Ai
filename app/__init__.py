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

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "scholarpath.db")

    from . import db
    db.init_app(app)

    from .routes import auth, opportunities, profile, saved
    app.register_blueprint(auth.bp)
    app.register_blueprint(opportunities.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(saved.bp)

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

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors.html", error_title="Page Not Found (404)", error_message="The page you requested could not be found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors.html", error_title="Server Error (500)", error_message="An internal error occurred. Please try again later."), 500

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
