import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY was not found in the .env file")
    app.config["SECRET_KEY"] = secret_key

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

    @app.route("/")
    def index():
        return render_template("index.html")

    return app