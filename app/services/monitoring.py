"""Source monitoring and change detection (FR-12, FR-14).

How it works
------------
1. For every tracked opportunity we download its official ``source_url``
   (politely: robots.txt is respected, a delay is kept between requests).
2. The page is reduced to its readable text (scripts, styles, menus removed)
   and hashed. The first time we see a page we store it as a *baseline*.
3. On later runs, if the hash differs, the old and new text are compared line
   by line. Changed lines are classified as deadline / eligibility / funding /
   status changes using keyword rules. Anything else is stored as "other" and
   flagged for manual review (the proposal says low-confidence changes must be
   reviewed by a person).
4. Every attempt (also failures) is written to ``source_checks``.

Run it with::

    flask --app run check-sources            # all opportunities
    flask --app run check-sources --saved-only

The module uses only the Python standard library for fetching and parsing.
"""
import difflib
import hashlib
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser

import click

USER_AGENT = "ScholarPathBot/1.0 (university capstone project; respects robots.txt)"
TIMEOUT_SECONDS = 15
MAX_BYTES = 2_000_000          # refuse to read pages larger than this
MAX_STORED_CHARS = 200_000     # cap what we keep per snapshot
MIN_READABLE_CHARS = 200       # fewer characters => probably a JavaScript-only page
MIN_OTHER_LINES = 3            # uncategorised changes smaller than this are treated as noise
MAX_TEXT_PER_CHANGE = 600      # characters of old/new text kept per change record
DEFAULT_DELAY_SECONDS = 2.0


class FetchError(Exception):
    """The page could not be downloaded or read."""


class BlockedError(FetchError):
    """robots.txt does not allow automated access to this page."""


class HttpStatusError(FetchError):
    def __init__(self, code):
        super().__init__(f"HTTP {code}")
        self.code = code


# ---------------------------------------------------------------------------
# 1. Turning a web page into comparable text
# ---------------------------------------------------------------------------

_SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "head", "nav", "footer"}
_BLOCK_TAGS = {
    "p", "div", "li", "ul", "ol", "br", "tr", "td", "th", "table", "section", "article",
    "header", "main", "aside", "blockquote", "dd", "dt", "dl", "form", "pre",
    "h1", "h2", "h3", "h4", "h5", "h6",
}
# Lines that change on every visit and say nothing about the opportunity.
_IGNORED_LINE = re.compile(
    r"^(last (updated|modified|reviewed)|page (last )?updated|updated on|copyright|©|"
    r"all rights reserved|skip to (main )?content|cookie)",
    re.IGNORECASE,
)


def _clean(text):
    text = unicodedata.normalize("NFKC", text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines = []
        self._buffer = []
        self._skip_depth = 0

    def _flush(self):
        line = _clean(" ".join(self._buffer))
        self._buffer = []
        if line and not _IGNORED_LINE.match(line):
            self.lines.append(line)

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._buffer.append(data)

    def close(self):
        super().close()
        self._flush()


def extract_lines(html):
    """Return the readable text of an HTML page as a list of non-empty lines."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.lines


def plain_text_lines(text):
    lines = (_clean(line) for line in text.splitlines())
    return [line for line in lines if line and not _IGNORED_LINE.match(line)]


# ---------------------------------------------------------------------------
# 2. Downloading politely
# ---------------------------------------------------------------------------

class PageFetcher:
    """Callable ``fetcher(url) -> list of text lines``. Honors robots.txt."""

    def __init__(self, user_agent=USER_AGENT, timeout=TIMEOUT_SECONDS):
        self.user_agent = user_agent
        self.timeout = timeout
        self._robots = {}   # origin -> RobotFileParser

    def _get(self, url):
        request = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent,
            "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                content_type = response.headers.get("Content-Type", "")
                charset = response.headers.get_content_charset() or "utf-8"
        except urllib.error.HTTPError as error:
            raise HttpStatusError(error.code) from None
        except urllib.error.URLError as error:
            raise FetchError(f"network error: {error.reason}") from None
        except (TimeoutError, OSError) as error:
            raise FetchError(f"network error: {error}") from None
        if len(raw) > MAX_BYTES:
            raise FetchError("page is too large")
        return raw.decode(charset, errors="replace"), content_type.lower()

    def _robots_for(self, parts):
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin in self._robots:
            return self._robots[origin]
        parser = urllib.robotparser.RobotFileParser()
        try:
            body, _ = self._get(origin + "/robots.txt")
            parser.parse(body.splitlines())
        except HttpStatusError as error:
            if error.code >= 500:
                parser.disallow_all = True      # RFC 9309: server error => do not crawl
            else:
                parser.parse([])                # no robots.txt => allowed
        except FetchError as error:
            raise FetchError(f"could not read robots.txt ({error})") from None
        self._robots[origin] = parser
        return parser

    def __call__(self, url):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise FetchError("unsupported URL")
        if not self._robots_for(parts).can_fetch(self.user_agent, url):
            raise BlockedError("robots.txt does not allow automated access")
        body, content_type = self._get(url)
        if "html" in content_type:
            return extract_lines(body)
        if content_type.startswith("text/"):
            return plain_text_lines(body)
        raise FetchError(f"unsupported content type '{content_type or 'unknown'}'")


# ---------------------------------------------------------------------------
# 3. Comparing two versions and classifying the change
# ---------------------------------------------------------------------------

# Checked in this order; the first match wins.
CATEGORY_RULES = (
    ("status", re.compile(
        r"closed|no longer|not (currently )?accepting|now open|applications? (are |is )?(open|closed)"
        r"|opens? (on|in)|cancel|suspend|postpone|withdrawn|filled", re.I)),
    ("deadline", re.compile(
        r"deadline|apply by|closing date|closes|due date|application (period|window)|submission date"
        r"|must be received|no later than", re.I)),
    ("eligibility", re.compile(
        r"eligib|requirement|cgpa|gpa|ielts|toefl|duolingo|citizen|nationality|degree|qualif"
        r"|must (have|hold|be)|prerequisite|language|work experience|age limit", re.I)),
    ("funding", re.compile(
        r"fund|stipend|tuition|allowance|waiver|salary|grant|fee|living cost|per month|per year"
        r"|\b(usd|eur|gbp|sek|jpy|krw)\b|[$€£]", re.I)),
)

LABELS = {
    "status": "Application status wording changed",
    "deadline": "Deadline or application-period wording changed",
    "eligibility": "Eligibility or requirement wording changed",
    "funding": "Funding or fee wording changed",
    "other": "Page content changed (could not be classified)",
}


def classify_line(line):
    for category, pattern in CATEGORY_RULES:
        if pattern.search(line):
            return category
    return "other"


def _shorten(lines):
    text = "\n".join(lines)
    return text if len(text) <= MAX_TEXT_PER_CHANGE else text[:MAX_TEXT_PER_CHANGE - 1] + "…"


def classify_changes(old_lines, new_lines):
    """Compare two versions of a page; return a list of change dicts.

    Each dict has: change_type, old_text, new_text, summary, needs_review.
    Returns an empty list when only noise changed.
    """
    removed = {}
    added = {}
    changed_count = 0
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        for line in old_lines[i1:i2]:
            removed.setdefault(classify_line(line), []).append(line)
            changed_count += 1
        for line in new_lines[j1:j2]:
            added.setdefault(classify_line(line), []).append(line)
            changed_count += 1

    changes = []
    for category in ("status", "deadline", "eligibility", "funding"):
        old, new = removed.get(category, []), added.get(category, [])
        if old or new:
            changes.append(_change(category, old, new, needs_review=False))

    if not changes:
        old, new = removed.get("other", []), added.get("other", [])
        if len(old) + len(new) >= MIN_OTHER_LINES:
            changes.append(_change("other", old, new, needs_review=True))
    return changes


def _change(category, old, new, needs_review):
    summary = f"{LABELS[category]} ({len(old)} line(s) removed, {len(new)} added)."
    return {
        "change_type": category,
        "old_text": _shorten(old) or None,
        "new_text": _shorten(new) or None,
        "summary": summary,
        "needs_review": int(needs_review),
    }


# ---------------------------------------------------------------------------
# 4. Storing results
# ---------------------------------------------------------------------------

def _timestamp(now):
    return now.strftime("%Y-%m-%d %H:%M:%S")


def _log_check(db, opportunity_id, outcome, detail, now):
    db.execute(
        "INSERT INTO source_checks (opportunity_id, outcome, detail, checked_at) VALUES (?, ?, ?, ?)",
        (opportunity_id, outcome, detail, _timestamp(now)),
    )


def process_page(db, opportunity_id, lines, now=None):
    """Compare freshly fetched text with the stored snapshot and record the result.

    Returns (outcome, number_of_changes_recorded).
    """
    now = now or datetime.now(timezone.utc)
    text = "\n".join(lines)[:MAX_STORED_CHARS]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    if len(text) < MIN_READABLE_CHARS:
        _log_check(db, opportunity_id, "error",
                   "page has too little readable text (it may need JavaScript to display)", now)
        return "error", 0

    previous = db.execute(
        "SELECT content_hash, content_text FROM source_snapshots "
        "WHERE opportunity_id = ? ORDER BY id DESC LIMIT 1", (opportunity_id,)
    ).fetchone()

    # A successful visit means "we looked at the official page today" (FR-14).
    db.execute("UPDATE opportunities SET last_checked = ? WHERE id = ?",
               (now.strftime("%Y-%m-%d"), opportunity_id))

    if previous is None:
        _add_snapshot(db, opportunity_id, digest, text, now)
        _log_check(db, opportunity_id, "baseline", "first snapshot stored", now)
        return "baseline", 0

    if previous["content_hash"] == digest:
        _log_check(db, opportunity_id, "unchanged", None, now)
        return "unchanged", 0

    snapshot_id = _add_snapshot(db, opportunity_id, digest, text, now)
    changes = classify_changes(previous["content_text"].split("\n"), text.split("\n"))
    for change in changes:
        db.execute(
            "INSERT INTO source_changes (opportunity_id, snapshot_id, detected_at, change_type, "
            "old_text, new_text, summary, needs_review) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (opportunity_id, snapshot_id, _timestamp(now), change["change_type"],
             change["old_text"], change["new_text"], change["summary"], change["needs_review"]),
        )
    if changes:
        _log_check(db, opportunity_id, "changed",
                   ", ".join(c["change_type"] for c in changes), now)
        return "changed", len(changes)
    _log_check(db, opportunity_id, "minor", "text differs but only in ignorable lines", now)
    return "minor", 0


def _add_snapshot(db, opportunity_id, digest, text, now):
    cursor = db.execute(
        "INSERT INTO source_snapshots (opportunity_id, content_hash, content_text, fetched_at) "
        "VALUES (?, ?, ?, ?)", (opportunity_id, digest, text, _timestamp(now)),
    )
    return cursor.lastrowid


def run_monitoring(db, fetcher=None, only_saved=False, opportunity_id=None,
                   delay=DEFAULT_DELAY_SECONDS, sleep=time.sleep, now=None, progress=None):
    """Check opportunity pages and return a summary dict.

    Opportunities that share one source URL (e.g. the Master's and PhD record of
    the same programme) are downloaded only once.
    """
    fetcher = fetcher or PageFetcher()
    now = now or datetime.now(timezone.utc)

    conditions, params = [], []
    if opportunity_id is not None:
        conditions.append("id = ?")
        params.append(opportunity_id)
    if only_saved:
        conditions.append("id IN (SELECT opportunity_id FROM saved_opportunities)")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        f"SELECT id, title, source_url FROM opportunities {where} ORDER BY id", params
    ).fetchall()

    by_url = {}
    for row in rows:
        by_url.setdefault(row["source_url"], []).append(row)

    summary = {"checked": 0, "baseline": 0, "unchanged": 0, "changed": 0,
               "minor": 0, "blocked": 0, "error": 0, "changes": 0}

    for position, (url, group) in enumerate(by_url.items()):
        if position and delay:
            sleep(delay)
        try:
            lines = fetcher(url)
            failure = None
        except BlockedError as error:
            lines, failure = None, ("blocked", str(error))
        except Exception as error:      # one bad page must never stop the whole run
            lines, failure = None, ("error", str(error) or error.__class__.__name__)

        for row in group:
            summary["checked"] += 1
            if failure:
                outcome, count = failure[0], 0
                _log_check(db, row["id"], failure[0], failure[1], now)
            else:
                outcome, count = process_page(db, row["id"], lines, now)
            summary[outcome] += 1
            summary["changes"] += count
            if progress:
                progress(row, outcome, count, failure[1] if failure else None)
        db.commit()
    return summary


# ---------------------------------------------------------------------------
# 5. Reading results back (used by the web pages)
# ---------------------------------------------------------------------------

CHANGE_LABELS = {
    "deadline": "Deadline", "eligibility": "Eligibility", "funding": "Funding",
    "status": "Status", "other": "Other",
}


def recent_changes_for_opportunity(db, opportunity_id, limit=5):
    return db.execute(
        "SELECT * FROM source_changes WHERE opportunity_id = ? ORDER BY id DESC LIMIT ?",
        (opportunity_id, limit),
    ).fetchall()


def last_check_for_opportunity(db, opportunity_id):
    return db.execute(
        "SELECT * FROM source_checks WHERE opportunity_id = ? ORDER BY id DESC LIMIT 1",
        (opportunity_id,),
    ).fetchone()


def changes_for_user(db, user_id, limit=100):
    """Changes on the opportunities this user has saved, newest first."""
    return db.execute(
        """
        SELECT c.*, o.title, o.provider, o.source_url, s.status AS saved_status
        FROM source_changes c
        JOIN opportunities o ON o.id = c.opportunity_id
        JOIN saved_opportunities s ON s.opportunity_id = c.opportunity_id AND s.user_id = ?
        ORDER BY c.id DESC LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()


# ---------------------------------------------------------------------------
# 6. Command line: flask --app run check-sources
# ---------------------------------------------------------------------------

@click.command("check-sources")
@click.option("--saved-only", is_flag=True, help="Only check opportunities that some user has saved.")
@click.option("--id", "opportunity_id", type=int, default=None, help="Check one opportunity by id.")
@click.option("--delay", type=float, default=DEFAULT_DELAY_SECONDS, show_default=True,
              help="Seconds to wait between different websites.")
def check_sources_command(saved_only, opportunity_id, delay):
    """Re-check official pages and record any detected changes."""
    from app.db import get_db

    def show(row, outcome, count, detail):
        extra = f" ({count} change(s))" if count else (f" - {detail}" if detail else "")
        click.echo(f"[{outcome:9}] #{row['id']} {row['title']}{extra}")

    db = get_db()
    summary = run_monitoring(db, only_saved=saved_only, opportunity_id=opportunity_id,
                             delay=delay, progress=show)
    click.echo(
        "Checked {checked}: {baseline} new baseline, {unchanged} unchanged, {changed} changed "
        "({changes} change records), {minor} minor, {blocked} blocked, {error} errors.".format(**summary)
    )


def init_app(app):
    app.cli.add_command(check_sources_command)
