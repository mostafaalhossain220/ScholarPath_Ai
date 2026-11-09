import re

import pytest

from app import create_app
from app.db import get_db, init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client with a fresh temporary database and two sample opportunities."""
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    app = create_app()
    app.config.update(TESTING=True, DATABASE=str(tmp_path / "test.db"))
    with app.app_context():
        init_db()
        db = get_db()
        for title in ("Sample PhD A", "Sample Masters B"):
            db.execute(
                "INSERT INTO opportunities (title, provider, type, degree_level, source_url) "
                "VALUES (?, 'Test Univ', 'phd', 'phd', 'https://example.com')", (title,))
        db.commit()
    return app.test_client()


def token(client, url="/auth/login"):
    """Read the CSRF token from a page, the way a browser form would send it."""
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def register(client, **overrides):
    data = {"name": "Rafi", "email": "rafi@example.com",
            "password": "secret123", "confirm": "secret123"}
    data.update(overrides)
    data["csrf_token"] = token(client, "/auth/register")
    return client.post("/auth/register", data=data)


def login(client, email="rafi@example.com", password="secret123"):
    return client.post("/auth/login", data={
        "email": email, "password": password,
        "csrf_token": token(client, "/auth/login")})


def register_and_login(client, **overrides):
    register(client, **overrides)
    return login(client, email=overrides.get("email", "rafi@example.com"))
