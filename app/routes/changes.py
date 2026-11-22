from flask import Blueprint, g, render_template

from app.db import get_db
from app.routes.auth import login_required
from app.services.monitoring import CHANGE_LABELS, changes_for_user

bp = Blueprint("changes", __name__, url_prefix="/changes")


@bp.route("/")
@login_required
def updates():
    """Detected changes on the opportunities this user has saved."""
    changes = changes_for_user(get_db(), g.user["id"])
    return render_template("changes/list.html", changes=changes, labels=CHANGE_LABELS)
