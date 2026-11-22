# ScholarPath AI

**Intelligent Scholarship and Funded PhD Matching**: a decision-support web app that helps students find fully funded Master's scholarships and funded PhD positions, check their eligibility requirement by requirement, and track applications.

> SE 331 Software Engineering Design Capstone · Section D1 · Batch 41 · Daffodil International University
> Team: Mostafa Al Hossain (232-35-220) · Farjana Boby Rea (232-35-360) · Ayesha Siddika (232-35-653)
> Supervisor: Md. Mahedi Hasan, Senior Lecturer, Department of Software Engineering

ScholarPath AI is advisory only. It does **not** predict admission or funding, and it does not submit applications. Users must always confirm details on the official provider page.

---

## Features (current prototype)

| Area | What it does |
|---|---|
| **Accounts** | Register, log in, log out. Passwords are hashed, forms are CSRF-protected, sessions are hardened. |
| **Academic profile** | Target degree, field, CGPA (4.0 scale), IELTS, preferred countries, funding need, skills, research interests. |
| **Student dashboard** | Profile-completeness ring, count of possible matches, saved/tracked count, deadlines in the next 60 days, top 3 picks for the profile, tracker summary. |
| **Find opportunities** | Keyword search and filters for degree, country, field and deadline. Shows provider, funding, deadline, source and last-checked date. |
| **Opportunity & evidence screen** | Full details, a requirement-by-requirement **eligibility check** (Satisfied / Not satisfied / Unclear / Not provided), the official requirement text as evidence, the source URL, last-checked date and a verification warning. |
| **AI matching** *(optional)* | Ranks opportunities with Sentence Transformers semantic similarity plus a keyword baseline. Only enabled when `sentence-transformers` is installed. |
| **Source monitoring** | `flask --app run check-sources` re-downloads the official pages (respecting robots.txt), compares them with the stored copy and records deadline / eligibility / funding / status changes. Changes on saved opportunities are listed on the **Updates** page and on each detail page. |
| **Saved & tracking** | Save opportunities, set status (saved / preparing / applied / dropped) and keep notes. |
| **UI** | Light and night mode, soft animated sakura background, scroll-reveal and count-up animations. Respects the system "reduce motion" setting. |
| **Smooth navigation** | Main pages are preloaded in the background; clicking a link or applying filters swaps only the content area with a fade (`app/static/js/nav.js`), with no full page reload. Forms that change data still do a normal load. |

### Planned (not built yet)
- RAG retrieval of official-source passages (FAISS/Chroma + LLM)
- PhD research-fit explanation
- Email alerts for detected changes (the `source_changes.notified` column is ready for it)
- Email-preferences page
- Admin / source management page

---

## Tech stack

- **Backend:** Python 3, Flask 3, SQLite (`instance/scholarpath.db`)
- **Frontend:** Jinja2 templates, Bootstrap 5.3, Bootstrap Icons, Flatpickr, custom CSS/JS
- **AI (optional):** `sentence-transformers` (model `all-MiniLM-L6-v2`)
- **Testing:** pytest

---

## Run it locally

```bash
# 1. Get the code
git clone https://github.com/mostafaalhossain220/ScholarPath_Ai.git
cd ScholarPath_Ai

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-dev.txt
#   sentence-transformers is large (it pulls in PyTorch). If you only need the
#   core app, install Flask and friends from requirements.txt without it.
#   The app still starts; only the "AI match" page is hidden.

# 4. Create a .env file with a secret key (required)
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .env

# 5. Create the database tables and load the opportunity data
flask --app run init-db
python import_data.py

# 6. Start the development server
python run.py
```

Then open **http://127.0.0.1:5000**, create an account, fill in **My profile**, and open the dashboard.

`.env`, `instance/` and `*.db` are git-ignored, so each developer has their own local database and secret.

---

## Run the tests

```bash
python -m pytest -q
```

Tests use a temporary database, so they never touch your local data. `tests/test_matching_optional.py` checks that the app still starts when `sentence-transformers` is missing.

The root scripts `compare_test.py`, `ranking_test.py`, `embedding_test.py` and `semantic_db_test.py` are manual experiments for the matching model. They are not part of the pytest suite and need `sentence-transformers`.

---

## Project structure

```
ScholarPath_Ai/
├── run.py                    # Entry point: python run.py
├── import_data.py            # Load / update data/opportunities.csv into SQLite
├── data/opportunities.csv    # Curated, manually verified opportunities
├── app/
│   ├── __init__.py           # App factory, security headers, error pages, dashboard route
│   ├── db.py                 # SQLite connection + `flask init-db`
│   ├── schema.sql            # users, profiles, opportunities, saved_opportunities
│   ├── routes/               # auth, profile, opportunities, saved, matching (optional)
│   ├── services/
│   │   ├── dashboard.py      # Dashboard stats, deadlines, top picks
│   │   ├── eligibility.py    # Rule-based requirement checks (degree, CGPA, IELTS)
│   │   ├── keyword_matcher.py
│   │   ├── semantic_matcher.py
│   │   └── ranking.py
│   ├── templates/            # Jinja pages (base, index/dashboard, auth, profile, ...)
│   └── static/               # css/style.css, js/main.js, js/sakura.js, img/
└── tests/                    # pytest suite
```

---

## How the eligibility check works

For each opportunity, `app/services/eligibility.py` compares the student's profile with the values stored for that opportunity:

| Requirement | Satisfied | Not satisfied | Unclear | Not provided |
|---|---|---|---|---|
| Degree level | Profile target degree matches | Different degree | Profile has no target degree | Opportunity has no degree level |
| CGPA | Profile ≥ minimum | Profile < minimum | Profile has no CGPA | Opportunity states no minimum |
| IELTS | Profile ≥ minimum | Profile < minimum | Profile has no IELTS | Opportunity states no minimum |

The overall result is **Not satisfied** if any check fails, **Needs verification** if any check is unclear or not provided, and otherwise **Meets the listed checks**. Missing information is never guessed. The official requirement text and the source link are shown next to the result so the student can verify it.

---

## Adding opportunities

Edit `data/opportunities.csv` (columns: `title, provider, type, degree_level, field, country, funding, min_cgpa, min_ielts, deadline, description, requirements_text, source_url, last_checked`) and run `python import_data.py` again. Existing rows (same title + provider + degree level) are updated, and new rows are inserted. Dates are accepted as `YYYY-MM-DD` or `M/D/YYYY`.

Only collect data from official sources, and respect each site's terms, robots rules and rate limits.

---

## Limitations

- Eligibility currently checks only degree level, CGPA and IELTS. Other conditions (nationality, work experience, documents) appear only as the official text.
- The opportunity collection is a small, manually verified set. Information can change after the last-checked date.
- Match scores show relevance, not admission probability.

---

## Source monitoring (change detection)

```bash
# one-time: add the new tables to an existing database (safe, keeps your data)
flask --app run init-db

# check every opportunity (waits 2 s between different websites)
flask --app run check-sources

# only opportunities that some user has saved / one opportunity by id
flask --app run check-sources --saved-only
flask --app run check-sources --id 5
```

* The first run only stores a **baseline** copy of each page. Changes can be detected from the second run on.
* Pages that cannot be read (blocked by robots.txt, network error, JavaScript-only page) are logged in `source_checks` and shown as "could not read the page".
* Uncategorised changes are marked **Needs manual review**. Detections are advisory, so always confirm on the official page.
* To run it automatically, schedule the same command (cron, or a PythonAnywhere *Scheduled task*), e.g. once a day.

