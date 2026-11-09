import pytest

from conftest import login, register, token


def test_pages_load(client):
    assert client.get("/auth/register").status_code == 200
    assert client.get("/auth/login").status_code == 200


def test_register_then_login_and_logout(client):
    assert register(client).status_code == 302
    assert login(client).status_code == 302
    assert "Hi, Rafi" in client.get("/").get_data(as_text=True)
    client.post("/auth/logout", data={"csrf_token": token(client, "/")})
    assert "Log in" in client.get("/").get_data(as_text=True)


def test_password_is_hashed(client):
    register(client)
    with client.application.app_context():
        from app.db import get_db
        stored = get_db().execute("SELECT password_hash FROM users").fetchone()[0]
    assert stored != "secret123" and stored.startswith(("scrypt:", "pbkdf2:"))


@pytest.mark.parametrize("field,value,message", [
    ("name", "", "Name is required"),
    ("email", "not-an-email", "valid email"),
    ("password", "short1", "at least 8"),
    ("password", "onlyletters", "one letter and one number"),
    ("confirm", "different123", "do not match"),
])
def test_registration_validation(client, field, value, message):
    response = register(client, **{field: value})
    assert response.status_code == 200
    assert message in response.get_data(as_text=True)


def test_duplicate_email_rejected(client):
    register(client)
    response = register(client, email="RAFI@example.com")
    assert "already exists" in response.get_data(as_text=True)


def test_wrong_password_and_unknown_email_same_message(client):
    register(client)
    a = login(client, password="wrongpass1").get_data(as_text=True)
    b = login(client, email="nobody@example.com").get_data(as_text=True)
    assert "Incorrect email or password." in a and "Incorrect email or password." in b


def test_post_without_csrf_token_is_rejected(client):
    response = client.post("/auth/login", data={"email": "a@b.com", "password": "x"})
    assert response.status_code == 400


def test_login_redirects_to_next_url(client):
    register(client)
    response = client.post("/auth/login?next=/profile/", data={
        "email": "rafi@example.com", "password": "secret123",
        "csrf_token": token(client, "/auth/login")
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile/"

