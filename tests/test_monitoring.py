import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.db import get_db, init_db
from app.services import monitoring
from app.services.monitoring import (
    BlockedError, FetchError, PageFetcher, classify_changes, classify_line,
    extract_lines, process_page, run_monitoring,
)
from conftest import register_and_login

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)

PAGE_V1 = [
    "PhD in Data Science",
    "The department offers fully funded doctoral positions in data science and machine learning.",
    "Application deadline: 1 December 2026.",
    "Applicants must hold a Master's degree with a minimum CGPA of 3.5.",
    "IELTS overall 6.5 is required for international applicants.",
    "Successful candidates receive a stipend of 2000 EUR per month and tuition waiver.",
]


def edit(lines, old_start, new_line):
    return [new_line if line.startswith(old_start) else line for line in lines]


@pytest.fixture
def db(client):
    """A database connection inside an app context (the `client` fixture builds the DB)."""
    app = client.application
    with app.app_context():
        yield get_db()


# ---------------------------------------------------------------- text extraction

def test_extract_lines_drops_scripts_menus_and_noise():
    html = """
    <html><head><title>ignored</title><style>p{color:red}</style></head>
    <body><nav><a>Home</a><a>Menu</a></nav>
      <h1>PhD  Position</h1>
      <script>var tracker = 1;</script>
      <p>Deadline:&nbsp;1 Dec <b>2026</b></p>
      <p>Last updated: 3 Nov 2026</p>
      <footer>Footer links</footer>
    </body></html>"""
    assert extract_lines(html) == ["PhD Position", "Deadline: 1 Dec 2026"]


# ---------------------------------------------------------------- classification

@pytest.mark.parametrize("line, expected", [
    ("Applications are now closed for this round.", "status"),
    ("Application deadline: 15 January 2027", "deadline"),
    ("Minimum IELTS score of 7.0 is required", "eligibility"),
    ("Stipend of 2000 EUR per month", "funding"),
    ("Welcome to our department", "other"),
])
def test_classify_line(line, expected):
    assert classify_line(line) == expected


def test_deadline_change_is_detected_and_classified():
    new = edit(PAGE_V1, "Application deadline", "Application deadline: 15 January 2027.")
    changes = classify_changes(PAGE_V1, new)
    assert [c["change_type"] for c in changes] == ["deadline"]
    assert "1 December 2026" in changes[0]["old_text"]
    assert "15 January 2027" in changes[0]["new_text"]
    assert changes[0]["needs_review"] == 0


def test_several_categories_in_one_change():
    new = edit(PAGE_V1, "Application deadline", "Application deadline: 15 January 2027.")
    new = edit(new, "IELTS", "IELTS overall 7.0 is required for international applicants.")
    kinds = {c["change_type"] for c in classify_changes(PAGE_V1, new)}
    assert kinds == {"deadline", "eligibility"}


def test_small_uncategorised_change_is_ignored_as_noise():
    new = PAGE_V1 + ["Photo gallery"]
    assert classify_changes(PAGE_V1, new) == []


def test_large_uncategorised_change_needs_manual_review():
    new = PAGE_V1 + ["Photo gallery", "Our campus", "Student life"]
    changes = classify_changes(PAGE_V1, new)
    assert len(changes) == 1
    assert changes[0]["change_type"] == "other" and changes[0]["needs_review"] == 1


# ---------------------------------------------------------------- storing results

def test_first_run_is_baseline_then_unchanged_then_changed(db):
    assert process_page(db, 1, PAGE_V1, NOW) == ("baseline", 0)
    assert process_page(db, 1, PAGE_V1, NOW) == ("unchanged", 0)

    new = edit(PAGE_V1, "Application deadline", "Application deadline: 15 January 2027.")
    assert process_page(db, 1, new, NOW) == ("changed", 1)

    assert db.execute("SELECT COUNT(*) FROM source_snapshots WHERE opportunity_id = 1").fetchone()[0] == 2
    change = db.execute("SELECT * FROM source_changes WHERE opportunity_id = 1").fetchone()
    assert change["change_type"] == "deadline" and change["notified"] == 0
    outcomes = [r["outcome"] for r in db.execute("SELECT outcome FROM source_checks ORDER BY id")]
    assert outcomes == ["baseline", "unchanged", "changed"]


def test_successful_check_updates_last_checked(db):
    process_page(db, 1, PAGE_V1, NOW)
    assert db.execute("SELECT last_checked FROM opportunities WHERE id = 1").fetchone()[0] == "2026-11-22"


def test_page_with_too_little_text_is_an_error_and_not_stored(db):
    assert process_page(db, 1, ["Loading..."], NOW) == ("error", 0)
    assert db.execute("SELECT COUNT(*) FROM source_snapshots").fetchone()[0] == 0
    check = db.execute("SELECT * FROM source_checks").fetchone()
    assert "JavaScript" in check["detail"]


def test_init_db_can_be_rerun_on_existing_database(db):
    db.execute("INSERT INTO opportunities (title, provider, type, degree_level, source_url) "
               "VALUES ('Keep me', 'X', 'phd', 'phd', 'https://x.example')")
    db.commit()
    init_db()   # must not fail or delete data
    assert db.execute("SELECT COUNT(*) FROM opportunities WHERE title = 'Keep me'").fetchone()[0] == 1


# ---------------------------------------------------------------- the whole run

def test_run_monitoring_handles_changes_blocks_and_errors(db):
    # make the two sample opportunities use different pages, add a third and fourth
    db.execute("UPDATE opportunities SET source_url = 'https://a.example/1' WHERE id = 1")
    db.execute("UPDATE opportunities SET source_url = 'https://b.example/2' WHERE id = 2")
    db.execute("INSERT INTO opportunities (title, provider, type, degree_level, source_url) "
               "VALUES ('Blocked one', 'T', 'phd', 'phd', 'https://c.example/3')")
    db.execute("INSERT INTO opportunities (title, provider, type, degree_level, source_url) "
               "VALUES ('Broken one', 'T', 'phd', 'phd', 'https://d.example/4')")
    db.commit()

    pages = {"https://a.example/1": PAGE_V1, "https://b.example/2": PAGE_V1}

    def fetcher(url):
        if "c.example" in url:
            raise BlockedError("robots.txt does not allow automated access")
        if "d.example" in url:
            raise FetchError("HTTP 500")
        return pages[url]

    first = run_monitoring(db, fetcher=fetcher, delay=0, now=NOW)
    assert first["baseline"] == 2 and first["blocked"] == 1 and first["error"] == 1

    pages["https://a.example/1"] = edit(PAGE_V1, "Applicants must", "Applicants must hold a Master's degree with a minimum CGPA of 3.8.")
    second = run_monitoring(db, fetcher=fetcher, delay=0, now=NOW)
    assert second["changed"] == 1 and second["unchanged"] == 1 and second["changes"] == 1
    assert db.execute("SELECT change_type FROM source_changes").fetchone()[0] == "eligibility"


def test_opportunities_sharing_a_url_are_downloaded_once(db):
    db.execute("UPDATE opportunities SET source_url = 'https://same.example/page'")
    db.commit()
    calls = []

    def fetcher(url):
        calls.append(url)
        return PAGE_V1

    summary = run_monitoring(db, fetcher=fetcher, delay=0, now=NOW)
    assert len(calls) == 1 and summary["checked"] == 2 and summary["baseline"] == 2


def test_saved_only_checks_only_saved_opportunities(client):
    register_and_login(client)
    from conftest import token
    client.post("/saved/add/1", data={"csrf_token": token(client, "/opportunities/1")})
    with client.application.app_context():
        db = get_db()
        db.execute("UPDATE opportunities SET source_url = 'https://a.example/' || id")
        db.commit()
        seen = []
        run_monitoring(db, fetcher=lambda url: seen.append(url) or PAGE_V1,
                       only_saved=True, delay=0, now=NOW)
    assert seen == ["https://a.example/1"]


def test_delay_is_applied_between_different_sites(db):
    db.execute("UPDATE opportunities SET source_url = 'https://x.example/' || id")
    db.commit()
    sleeps = []
    run_monitoring(db, fetcher=lambda url: PAGE_V1, delay=2.0, sleep=sleeps.append, now=NOW)
    assert sleeps == [2.0]


# ---------------------------------------------------------------- web pages

def test_updates_page_requires_login(client):
    response = client.get("/changes/")
    assert response.status_code == 302 and "/auth/login" in response.headers["Location"]


def test_updates_page_shows_changes_only_for_saved_opportunities(client):
    from conftest import token
    register_and_login(client)
    client.post("/saved/add/1", data={"csrf_token": token(client, "/opportunities/1")})
    with client.application.app_context():
        db = get_db()
        process_page(db, 1, PAGE_V1, NOW)
        process_page(db, 1, edit(PAGE_V1, "Application deadline", "Application deadline: 15 January 2027."), NOW)
        process_page(db, 2, PAGE_V1, NOW)
        process_page(db, 2, edit(PAGE_V1, "IELTS", "IELTS overall 7.5 is required for international applicants."), NOW)
        db.commit()
    page = client.get("/changes/").get_data(as_text=True)
    assert "Sample PhD A" in page and "15 January 2027" in page
    assert "Sample Masters B" not in page


def test_updates_page_empty_state(client):
    register_and_login(client)
    assert "No changes detected yet" in client.get("/changes/").get_data(as_text=True)


def test_detail_page_shows_monitoring_card(client):
    page = client.get("/opportunities/1").get_data(as_text=True)
    assert "not been checked automatically yet" in page
    with client.application.app_context():
        db = get_db()
        process_page(db, 1, PAGE_V1, NOW)
        process_page(db, 1, edit(PAGE_V1, "Application deadline", "Application deadline: 15 January 2027."), NOW)
        db.commit()
    page = client.get("/opportunities/1").get_data(as_text=True)
    assert "Deadline or application-period wording changed" in page


# ---------------------------------------------------------------- real HTTP (local server)

class _Handler(BaseHTTPRequestHandler):
    robots = "User-agent: *\nDisallow: /private\n"
    body = "<html><body>" + "".join(f"<p>{line}</p>" for line in PAGE_V1) + "</body></html>"

    def do_GET(self):
        if self.path == "/robots.txt":
            payload, ctype = self.robots, "text/plain"
        elif self.path == "/pdf":
            payload, ctype = "x", "application/pdf"
        else:
            payload, ctype = self.body, "text/html; charset=utf-8"
        data = payload.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def local_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_page_fetcher_downloads_and_extracts_text(local_server):
    lines = PageFetcher()(local_server + "/page")
    assert "Application deadline: 1 December 2026." in lines


def test_page_fetcher_respects_robots_txt(local_server):
    with pytest.raises(BlockedError):
        PageFetcher()(local_server + "/private/call")


def test_page_fetcher_rejects_unsupported_content_and_urls(local_server):
    with pytest.raises(FetchError):
        PageFetcher()(local_server + "/pdf")
    with pytest.raises(FetchError):
        PageFetcher()("file:///etc/passwd")
