from conftest import register_and_login, token


def post(client, url, page="/saved/", **data):
    data["csrf_token"] = token(client, page)
    return client.post(url, data=data)


def test_tracker_requires_login(client):
    response = client.get("/saved/")
    assert response.status_code == 302 and "/auth/login" in response.headers["Location"]


def test_detail_page_prompts_login_when_logged_out(client):
    assert "Log in to save" in client.get("/opportunities/1").get_data(as_text=True)


def test_save_shows_in_tracker_and_marks_detail(client):
    register_and_login(client)
    assert post(client, "/saved/add/1", page="/opportunities/1").status_code == 302
    assert "Sample PhD A" in client.get("/saved/").get_data(as_text=True)
    assert "Saved" in client.get("/opportunities/1").get_data(as_text=True)


def test_saving_twice_does_not_duplicate(client):
    register_and_login(client)
    post(client, "/saved/add/1", page="/opportunities/1")
    response = post(client, "/saved/add/1", page="/opportunities/1")
    assert response.status_code == 302
    assert client.get("/saved/").get_data(as_text=True).count("Sample PhD A") == 1


def test_save_unknown_opportunity_is_404(client):
    register_and_login(client)
    assert post(client, "/saved/add/999", page="/opportunities/1").status_code == 404


def test_update_status_and_note(client):
    register_and_login(client)
    post(client, "/saved/add/1", page="/opportunities/1")
    post(client, "/saved/1/update", status="applied", note="Letters ready")
    page = client.get("/saved/").get_data(as_text=True)
    assert "Letters ready" in page and 'value="applied" selected' in page


def test_status_filter(client):
    register_and_login(client)
    post(client, "/saved/add/1", page="/opportunities/1")
    post(client, "/saved/add/2", page="/opportunities/1")
    post(client, "/saved/1/update", status="applied", note="")
    page = client.get("/saved/?status=applied").get_data(as_text=True)
    assert "Sample PhD A" in page and "Sample Masters B" not in page


def test_invalid_status_and_long_note_rejected(client):
    register_and_login(client)
    post(client, "/saved/add/1", page="/opportunities/1")
    post(client, "/saved/1/update", status="hacked", note="")
    post(client, "/saved/1/update", status="applied", note="x" * 501)
    page = client.get("/saved/").get_data(as_text=True)
    assert 'value="saved" selected' in page


def test_remove(client):
    register_and_login(client)
    post(client, "/saved/add/1", page="/opportunities/1")
    post(client, "/saved/1/remove")
    assert "Nothing here yet" in client.get("/saved/").get_data(as_text=True)


def test_user_cannot_touch_another_users_saved_item(client):
    register_and_login(client)
    post(client, "/saved/add/1", page="/opportunities/1")
    client.post("/auth/logout", data={"csrf_token": token(client, "/")})
    register_and_login(client, email="other@example.com", name="Other")
    assert post(client, "/saved/1/update", status="dropped", note="").status_code == 404
    assert post(client, "/saved/1/remove").status_code == 404
    assert "Sample PhD A" not in client.get("/saved/").get_data(as_text=True)


def test_post_without_csrf_rejected(client):
    register_and_login(client)
    assert client.post("/saved/add/1", data={}).status_code == 400
