-- Users: login accounts
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Profiles: one academic profile per user
CREATE TABLE IF NOT EXISTS profiles (
    user_id             INTEGER PRIMARY KEY,
    cgpa                REAL,
    ielts               REAL,
    target_degree       TEXT CHECK (target_degree IN ('masters', 'phd')),
    field               TEXT,
    preferred_countries TEXT,
    research_interests  TEXT,
    skills              TEXT,
    funding_need        TEXT,
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Opportunities: scholarships and funded PhD positions
CREATE TABLE IF NOT EXISTS opportunities (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    provider         TEXT NOT NULL,
    type             TEXT NOT NULL CHECK (type IN ('scholarship', 'phd', 'masters', 'admission_and_scholarship')),
    degree_level     TEXT NOT NULL CHECK (degree_level IN ('masters', 'phd')),
    field            TEXT,
    country          TEXT,
    funding          TEXT,
    min_cgpa         REAL,
    min_ielts        REAL,
    deadline         TEXT,
    description      TEXT,
    requirements_text TEXT,
    source_url       TEXT NOT NULL,
    last_checked     TEXT
);

-- Saved opportunities: which user saved which opportunity
CREATE TABLE IF NOT EXISTS saved_opportunities (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    opportunity_id INTEGER NOT NULL,
    status         TEXT NOT NULL DEFAULT 'saved'
                   CHECK (status IN ('saved', 'preparing', 'applied', 'dropped')),
    note           TEXT,
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, opportunity_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE
);