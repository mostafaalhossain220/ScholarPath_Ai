import sys

import app.routes


def test_app_still_starts_when_matching_dependencies_are_missing(monkeypatch, client):
    """If sentence-transformers is not installed, only the matching page is skipped."""
    from app import create_app

    monkeypatch.setitem(sys.modules, "app.routes.matching", None)  # makes the import fail
    monkeypatch.delattr(app.routes, "matching", raising=False)
    flask_app = create_app()
    page = flask_app.test_client().get("/")
    assert page.status_code == 200
    assert "Find matches" not in page.get_data(as_text=True)
    assert flask_app.jinja_env.globals["matching_enabled"] is False
