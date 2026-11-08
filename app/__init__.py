import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY .env file-এ পাওয়া যায়নি")
    app.config["SECRET_KEY"] = secret_key

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "scholarpath.db")

    @app.route("/")
    def index():
        return render_template("index.html")

    return app