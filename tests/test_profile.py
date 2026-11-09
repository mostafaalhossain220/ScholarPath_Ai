import pytest

from conftest import register_and_login, token


def save_profile(client, **overrides):
    data = {"cgpa": "3.5", "ielts": "6.5", "target_degree": "phd", "field": "Computer Science",
            "preferred_countries": "Sweden, Germany", "research_interests": "machine learning",
            "skills": "Python, Flask", "funding_need": "full"}
    data.update(overrides)
    data["csrf_token"] = token(client, "/profile/")
    return client.post("/profile/", data=data)


def test_profile_requires_login(client):
    response = client.get("/profile/")
    assert response.status_code == 302 and "/auth/login" in response.headers["Location"]


def test_save_and_reload_profile(client):
    register_and_login(client)
    assert save_profile(client).status_code == 302
    page = client.get("/profile/").get_data(as_text=True)
    assert 'value="3.5"' in page and 'value="Computer Science"' in page and 'value="Sweden, Germany"' in page


def test_profile_update_replaces_old_values(client):
    register_and_login(client)
    save_profile(client)
    save_profile(client, cgpa="3.9", field="Data Science")
    page = client.get("/profile/").get_data(as_text=True)
    assert 'value="3.9"' in page and 'value="Data Science"' in page and 'value="Computer Science"' not in page


def test_empty_profile_is_allowed(client):
    register_and_login(client)
    response = save_profile(client, cgpa="", ielts="", target_degree="", field="",
                            preferred_countries="", research_interests="", skills="", funding_need="")
    assert response.status_code == 302


@pytest.mark.parametrize("field,value,message", [
    ("cgpa", "abc", "must be a number"),
    ("cgpa", "4.5", "between 0 and 4"),
    ("ielts", "10", "between 0 and 9"),
    ("target_degree", "bachelors", "Choose Master"),
    ("funding_need", "free-money", "Choose one of the listed"),
    ("skills", "x" * 501, "under 500 characters"),
])
def test_profile_validation(client, field, value, message):
    register_and_login(client)
    response = save_profile(client, **{field: value})
    assert response.status_code == 200 and message in response.get_data(as_text=True)


def test_profiles_are_per_user(client):
    register_and_login(client)
    save_profile(client, field="Computer Science")
    client.post("/auth/logout", data={"csrf_token": token(client, "/")})
    register_and_login(client, email="other@example.com", name="Other")
    assert 'value="Computer Science"' not in client.get("/profile/").get_data(as_text=True)
