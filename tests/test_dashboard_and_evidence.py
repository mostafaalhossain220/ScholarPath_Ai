"""Tests for the student dashboard and the opportunity eligibility/evidence screen."""
from datetime import date, timedelta

from app.services.dashboard import days_until, profile_completeness
from tests.conftest import register_and_login, token


def save_profile(client, **values):
    data = {
        "cgpa": "3.6", "ielts": "7.0", "target_degree": "phd", "field": "Computer Science",
        "preferred_countries": "Germany", "research_interests": "NLP",
        "skills": "Python", "funding_need": "full",
    }
    data.update(values)
    data["csrf_token"] = token(client, "/profile/")
    return client.post("/profile/", data=data)


def set_opportunity(client, opportunity_id, **columns):
    """Update columns on a sample opportunity directly in the test database."""
    from app.db import get_db
    app = client.application
    with app.app_context():
        db = get_db()
        sets = ", ".join(f"{name} = ?" for name in columns)
        db.execute(f"UPDATE opportunities SET {sets} WHERE id = ?", (*columns.values(), opportunity_id))
        db.commit()


# ---------- service helpers ----------

def test_profile_completeness_counts_filled_fields():
    assert profile_completeness(None)[0] == 0
    full = {k: "x" for k in ("target_degree", "field", "cgpa", "ielts", "preferred_countries",
                             "funding_need", "skills", "research_interests")}
    assert profile_completeness(full) == (100, [])
    half = dict(full, skills="", research_interests=None, ielts=None, cgpa="  ")
    percent, missing = profile_completeness(half)
    assert percent == 50
    assert "Skills" in missing and "CGPA" in missing


def test_days_until_handles_bad_dates():
    today = date(2026, 11, 21)
    assert days_until("2026-11-30", today) == 9
    assert days_until("", today) is None
    assert days_until("not-a-date", today) is None


# ---------- dashboard page ----------

def test_dashboard_without_profile_prompts_to_create_one(client):
    register_and_login(client)
    html = client.get("/").get_data(as_text=True)
    assert "Your scholarship dashboard" in html
    assert "Create my profile" in html
    assert "Profile complete" in html


def test_dashboard_shows_top_picks_and_deadlines(client):
    register_and_login(client)
    save_profile(client)
    soon = (date.today() + timedelta(days=10)).isoformat()
    set_opportunity(client, 1, deadline=soon, min_cgpa=3.0)

    client.post("/saved/add/1", data={"csrf_token": token(client, "/opportunities/1")})

    html = client.get("/").get_data(as_text=True)
    assert "Top picks for your profile" in html
    assert "Sample PhD A" in html
    assert "Approaching deadlines" in html
    assert "is-urgent" in html  # 10 days left is highlighted
    assert "not an admission or funding prediction" in html


def test_dashboard_hides_opportunities_that_fail_a_requirement(client):
    register_and_login(client)
    save_profile(client, cgpa="2.5")
    set_opportunity(client, 1, min_cgpa=3.5)
    set_opportunity(client, 2, min_cgpa=3.5)
    html = client.get("/").get_data(as_text=True)
    assert "No open opportunity matches" in html


# ---------- eligibility & evidence screen ----------

def test_detail_asks_guest_to_log_in(client):
    html = client.get("/opportunities/1").get_data(as_text=True)
    assert "Your eligibility check" in html
    assert "Official requirements (evidence)" in html
    assert "Please verify before applying." in html


def test_detail_shows_requirement_statuses(client):
    register_and_login(client)
    save_profile(client, cgpa="3.2", ielts="")
    set_opportunity(client, 1, min_cgpa=3.5, min_ielts=6.5,
                    requirements_text="Applicants need a CGPA of 3.5.")
    html = client.get("/opportunities/1").get_data(as_text=True)
    assert "req-satisfied" in html       # degree level phd == phd
    assert "req-not_satisfied" in html   # CGPA 3.2 < 3.5
    assert "req-unclear" in html         # IELTS missing from profile
    assert "Applicants need a CGPA of 3.5." in html
    assert "https://example.com" in html


def test_detail_without_profile_links_to_profile(client):
    register_and_login(client)
    html = client.get("/opportunities/1").get_data(as_text=True)
    assert "Complete profile" in html


# ---------- guest landing page ----------

def test_home_signup_form_sends_every_field_register_needs(client):
    """The sign-up panel on the home page must post name, email, password and confirm."""
    html = client.get("/").get_data(as_text=True)
    signup = html.split('id="auth-signup-panel"', 1)[1]
    for field in ('name="name"', 'name="email"', 'name="password"', 'name="confirm"'):
        assert field in signup


def test_home_signup_creates_account(client):
    data = {"name": "Mina", "email": "mina@example.com", "password": "secret123",
            "confirm": "secret123", "csrf_token": token(client, "/")}
    response = client.post("/auth/register", data=data)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# ---------- country picker ----------

def test_split_countries_drops_notes_and_separators():
    from app.services.countries import split_countries
    assert split_countries("Belgium; Spain (confirm partners), Italy") == ["Belgium", "Spain", "Italy"]
    assert split_countries(None) == []


def test_listing_countries_come_from_the_database(client):
    set_opportunity(client, 1, country="UK")
    set_opportunity(client, 2, country="Spain; Netherlands (consortium)")
    from app.services.countries import listing_countries
    with client.application.app_context():
        assert listing_countries() == ["Netherlands", "Spain", "UK"]


def test_profile_country_picker_keeps_saved_value(client):
    register_and_login(client)
    save_profile(client, preferred_countries="UK, Germany")
    html = client.get("/profile/").get_data(as_text=True)
    assert "data-tag-input" in html
    assert 'name="preferred_countries" value="UK, Germany"' in html


# ---------- login redirect safety ----------

def test_is_safe_next_blocks_open_redirects():
    from app.routes.auth import is_safe_next
    for good in ("/", "/saved/", "/opportunities/?q=ai&country=UK"):
        assert is_safe_next(good)
    for bad in ("", "https://evil.com", "//evil.com", "/\\evil.com", "/\t/evil.com", "/\n/evil.com", "evil.com"):
        assert not is_safe_next(bad)


def test_login_never_redirects_off_site(client):
    from tests.conftest import register
    register(client)
    response = client.post("/auth/login", data={
        "email": "rafi@example.com", "password": "secret123", "next": "/\t/evil.com",
        "csrf_token": token(client, "/auth/login")})
    assert response.status_code == 302
    assert "evil.com" not in response.headers["Location"]


def test_login_still_returns_to_safe_next(client):
    from tests.conftest import register
    register(client)
    response = client.post("/auth/login", data={
        "email": "rafi@example.com", "password": "secret123", "next": "/saved/",
        "csrf_token": token(client, "/auth/login")})
    assert response.headers["Location"].endswith("/saved/")
