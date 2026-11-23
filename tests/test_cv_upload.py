import io
import zipfile

import pytest

from app.db import get_db
from app.services.cv_parser import CVError, extract_text, parse_cv
from conftest import register_and_login, token

CV_TEXT = """Farjana Boby Rea
Dhaka, Bangladesh | farjana@example.com

Objective
Seeking a fully funded PhD position in machine learning for healthcare.

Education
B.Sc. in Software Engineering (Data Science specialization), Daffodil International University, 2022-2026
CGPA: 3.67 out of 4.00

Language
IELTS Academic 2025: Overall 7.0 (Listening 7.5, Reading 7.5)

Research Interests
Explainable AI; Dengue risk prediction; Natural Language Processing

Skills
Python, SQL, Pandas, scikit-learn, Flask, Git, Docker
"""


def make_docx(lines):
    body = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in lines)
    xml = ('<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
           f'wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def make_pdf(lines):
    """A tiny valid one-page PDF whose text pypdf can read back."""
    def esc(t):
        return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = "BT /F1 11 Tf 40 780 Td 14 TL\n" + "\n".join(f"({esc(l)}) Tj T*" for l in lines) + "\nET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


# ------------------------------------------------------------------ parser

def test_parse_full_cv():
    r = parse_cv(CV_TEXT)["values"]
    assert r["cgpa"] == "3.67"
    assert r["ielts"] == "7"
    assert r["target_degree"] == "phd"
    assert r["field"] == "Software Engineering"
    assert "Explainable AI" in r["research_interests"]
    for skill in ("Python", "SQL", "Flask", "Docker", "scikit-learn"):
        assert skill in r["skills"]


@pytest.mark.parametrize("text, expected", [
    ("CGPA: 3.5/4.0", "3.5"), ("GPA 3.80 / 4.00", "3.8"), ("Result: 3.25/4", "3.25"),
    ("CGPA - 3.9", "3.9"),
])
def test_cgpa_formats(text, expected):
    assert parse_cv(text)["values"]["cgpa"] == expected


def test_cgpa_on_other_scale_is_not_guessed():
    result = parse_cv("CGPA: 8.4 out of 10")
    assert result["values"]["cgpa"] == ""
    assert any("4.0 scale" in n for n in result["notes"])


@pytest.mark.parametrize("text, expected", [
    ("IELTS: 6.5", "6.5"), ("IELTS Overall Band 7", "7"), ("IELTS (2024) overall 6.0", "6"),
])
def test_ielts_formats_ignore_years(text, expected):
    assert parse_cv(text)["values"]["ielts"] == expected


def test_degree_not_guessed_without_intent():
    assert parse_cv("B.Sc. in Computer Science. I like football.")["values"]["target_degree"] == ""


def test_masters_intent():
    assert parse_cv("Objective: apply for a fully funded Master's programme in AI")["values"]["target_degree"] == "masters"


def test_interest_fallback_uses_known_topics():
    values = parse_cv("Projects: built a natural language processing app and a deep learning model.")["values"]
    assert "natural language processing" in values["research_interests"]


def test_single_letter_skills_need_exact_case():
    assert "R" not in (parse_cv("I enjoy reading and running")["values"]["skills"] or "").split("; ")


# ------------------------------------------------------------------ file reading

def test_extract_txt_docx_pdf():
    assert "CGPA: 3.67" in extract_text("cv.txt", CV_TEXT.encode())
    assert "CGPA: 3.67" in extract_text("cv.docx", make_docx(CV_TEXT.splitlines()))
    assert "CGPA: 3.67" in extract_text("cv.pdf", make_pdf(CV_TEXT.splitlines()))


@pytest.mark.parametrize("name, data", [
    ("cv.exe", b"MZ" + b"x" * 100), ("cv.pdf", b"not a pdf at all" * 10),
    ("cv.docx", b"not a zip" * 10), ("cv.txt", b""), ("cv.txt", b"too short"),
])
def test_bad_files_are_rejected_with_friendly_error(name, data):
    with pytest.raises(CVError):
        extract_text(name, data)


# ------------------------------------------------------------------ web flow

def upload(client, name, data):
    return client.post("/cv/", data={"csrf_token": token(client, "/cv/"), "cv": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")


def test_cv_pages_require_login(client):
    for url in ("/cv/", "/cv/matches"):
        assert client.get(url).status_code == 302


def test_upload_shows_review_prefilled_and_does_not_save_yet(client):
    register_and_login(client)
    page = upload(client, "cv.txt", CV_TEXT.encode()).get_data(as_text=True)
    assert 'value="3.67"' in page and "Explainable AI" in page and "from CV" in page
    with client.application.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 0


def test_apply_saves_profile_and_shows_matches(client):
    register_and_login(client)
    with client.application.app_context():
        db = get_db()
        db.execute("UPDATE opportunities SET field='Machine Learning', description='Machine learning for healthcare', "
                   "min_cgpa=3.0 WHERE id=1")
        db.commit()
    data = {"cgpa": "3.67", "ielts": "7", "target_degree": "phd", "field": "Software Engineering",
            "preferred_countries": "", "research_interests": "machine learning; healthcare",
            "skills": "Python", "funding_need": "full", "csrf_token": token(client, "/cv/")}
    response = client.post("/cv/apply", data=data)
    assert response.status_code == 302 and response.headers["Location"].endswith("/cv/matches")
    page = client.get("/cv/matches").get_data(as_text=True)
    assert "Sample PhD A" in page and "Eligibility checklist" in page
    with client.application.app_context():
        row = get_db().execute("SELECT cgpa, target_degree FROM profiles").fetchone()
        assert row["cgpa"] == 3.67 and row["target_degree"] == "phd"


def test_apply_rejects_invalid_values_and_missing_csrf(client):
    register_and_login(client)
    bad = {"cgpa": "9", "ielts": "", "target_degree": "", "field": "", "preferred_countries": "",
           "research_interests": "", "skills": "", "funding_need": "", "csrf_token": token(client, "/cv/")}
    assert client.post("/cv/apply", data=bad).status_code == 400
    bad.pop("csrf_token")
    assert client.post("/cv/apply", data=bad).status_code == 400


def test_matches_without_profile_redirects_to_upload(client):
    register_and_login(client)
    assert "/cv/" in client.get("/cv/matches").headers["Location"]


def test_unreadable_cv_shows_error_not_crash(client):
    register_and_login(client)
    response = upload(client, "cv.pdf", b"%PDF-1.4 broken")
    assert response.status_code == 302
    assert "could not be read" in client.get("/cv/").get_data(as_text=True)


def test_oversized_upload_is_rejected(client):
    register_and_login(client)
    response = upload(client, "cv.txt", b"a" * (5 * 1024 * 1024))
    assert response.status_code == 413


def test_html_in_cv_is_escaped_on_review_page(client):
    register_and_login(client)
    evil = "CGPA: 3.5/4.0\nResearch Interests\n<script>alert(1)</script>\nSkills\n" + "x" * 50
    page = upload(client, "cv.txt", evil.encode()).get_data(as_text=True)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page   # it was read, and shown safely
    assert "<script>alert(1)</script>" not in page
