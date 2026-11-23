"""Read a CV (PDF, DOCX or TXT) and pull out the details ScholarPath AI needs.

Nothing here is AI magic: text is extracted from the file, then simple, explainable
rules (regular expressions and word lists) look for CGPA, IELTS, field of study,
skills, research interests and the degree the student is aiming for. The result is
only a *suggestion*. The student always reviews and corrects it before it is saved.

The CV file itself is never stored.
"""
import io
import re
import zipfile
from xml.etree import ElementTree

MAX_PDF_PAGES = 10
MAX_DOCX_XML_BYTES = 5_000_000      # protects against zip bombs
MAX_TEXT_CHARS = 60_000
MIN_TEXT_CHARS = 40

ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")


class CVError(Exception):
    """The CV could not be read. The message is safe to show to the student."""


# ---------------------------------------------------------------------------
# 1. File -> text
# ---------------------------------------------------------------------------

def extract_text(filename, data):
    """Return the text of an uploaded CV. Raises CVError with a friendly message."""
    name = (filename or "").lower()
    if not name.endswith(ALLOWED_EXTENSIONS):
        raise CVError("Please upload a PDF, DOCX or TXT file.")
    if not data:
        raise CVError("The file is empty.")

    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise CVError("This file is not a valid PDF.")
        text = _pdf_text(data)
    elif name.endswith(".docx"):
        if not data.startswith(b"PK"):
            raise CVError("This file is not a valid DOCX.")
        text = _docx_text(data)
    else:
        text = _txt_text(data)

    text = text.replace("\x00", " ")[:MAX_TEXT_CHARS]
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise CVError(
            "We could not read any text from this CV. Scanned or image-only CVs are not "
            "supported. Please upload a text-based PDF/DOCX, or fill in your profile by hand."
        )
    return text


def _pdf_text(data):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise CVError("PDF reading is not installed on this server (pip install pypdf).") from None
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise CVError("This PDF is password protected.")
        pages = reader.pages[:MAX_PDF_PAGES]
        return "\n".join((page.extract_text() or "") for page in pages)
    except CVError:
        raise
    except Exception:
        raise CVError("This PDF could not be read. Try exporting it again or upload a DOCX.") from None


def _docx_text(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_DOCX_XML_BYTES:
                raise CVError("This DOCX is too large to read.")
            xml = archive.read("word/document.xml")
    except CVError:
        raise
    except Exception:
        raise CVError("This DOCX could not be read.") from None

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        raise CVError("This DOCX could not be read.") from None
    lines = []
    for paragraph in root.iter(namespace + "p"):
        parts = []
        for node in paragraph.iter():
            if node.tag == namespace + "t" and node.text:
                parts.append(node.text)
            elif node.tag in (namespace + "tab", namespace + "br"):
                parts.append(" ")
        lines.append("".join(parts))
    return "\n".join(lines)


def _txt_text(data):
    for encoding in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


# ---------------------------------------------------------------------------
# 2. Text -> profile fields
# ---------------------------------------------------------------------------

SKILL_WORDS = [
    "Python", "R", "Java", "JavaScript", "TypeScript", "C++", "C#", "C", "MATLAB", "SQL",
    "PyTorch", "TensorFlow", "Keras", "scikit-learn", "Pandas", "NumPy", "SciPy", "OpenCV",
    "Hugging Face", "Transformers", "LangChain", "XGBoost", "LightGBM", "NLTK", "spaCy",
    "Flask", "Django", "FastAPI", "React", "Node.js", "HTML", "CSS", "Bootstrap",
    "Docker", "Git", "GitHub", "Linux", "AWS", "Azure", "Google Cloud", "Kubernetes",
    "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Power BI", "Tableau", "Excel",
    "Matplotlib", "Seaborn", "Jupyter", "Streamlit", "Spark", "Hadoop", "Kafka",
    "Statistics", "Data Analysis", "Data Visualization", "Data Mining", "Machine Learning",
    "Deep Learning", "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
    "Time Series", "Explainable AI", "SHAP", "LIME", "RAG", "Latent Semantic Analysis",
]

TOPIC_WORDS = [
    "natural language processing", "machine learning", "deep learning", "computer vision",
    "reinforcement learning", "explainable ai", "data mining", "data science", "bioinformatics",
    "medical imaging", "healthcare", "cyber security", "cybersecurity", "software engineering",
    "information retrieval", "recommender systems", "large language models", "generative ai",
    "time series", "robotics", "internet of things", "blockchain", "human-computer interaction",
    "big data", "cloud computing", "network security", "speech recognition", "text mining",
    "federated learning", "graph neural networks", "data engineering", "public health",
]

FIELD_WORDS = [
    "Computer Science", "Software Engineering", "Data Science", "Artificial Intelligence",
    "Machine Learning", "Information Technology", "Computer Engineering", "Cyber Security",
    "Electrical Engineering", "Electronic Engineering", "Information Systems", "Statistics",
    "Mathematics", "Physics", "Biotechnology", "Bioinformatics", "Business Administration",
    "Civil Engineering", "Mechanical Engineering", "Telecommunication Engineering",
]

_SECTION_STOP = (
    r"education|experience|work experience|employment|skills|technical skills|projects?|"
    r"publications?|awards?|honou?rs|references?|languages?|certifications?|courses|"
    r"thesis|training|activities|contact|summary|objective|profile|achievements?"
)
_HEADING = re.compile(rf"^\s*(?:{_SECTION_STOP})\s*:?\s*$", re.IGNORECASE)


def _find_cgpa(text):
    """CGPA on a 4.0 scale. Returns (value or None, note or None)."""
    note = None
    keyword = re.compile(
        r"(?:cgpa|c\.g\.p\.a|cpga|gpa|grade point average)\s*[:\-–=]?\s*\(?\s*"
        r"(\d{1,2}(?:\.\d{1,3})?)\s*(?:\)|\s)*(?:(?:/|out of|of)\s*(\d{1,2}(?:\.\d+)?))?",
        re.IGNORECASE,
    )
    for match in keyword.finditer(text):
        value = float(match.group(1))
        scale = float(match.group(2)) if match.group(2) else None
        if scale in (None, 4.0) and 0 < value <= 4.0:
            return round(value, 2), None
        if note is None:
            if scale not in (None, 4.0):
                note = (f"CGPA {match.group(1)} out of {match.group(2)} was found. "
                        "ScholarPath uses a 4.0 scale, so please enter it yourself.")
            elif value > 4.0:
                note = (f"CGPA {match.group(1)} was found but its scale is not 4.0. "
                        "Please enter your CGPA on a 4.0 scale yourself.")
    slash = re.search(r"\b([0-3]\.\d{1,2}|4\.0{1,2})\s*/\s*4(?:\.0+)?\b", text)
    if slash:
        return round(float(slash.group(1)), 2), None
    return None, note


def _find_ielts(text):
    """IELTS overall band (4.0 to 9.0, half steps)."""
    for match in re.finditer(r"ielts", text, re.IGNORECASE):
        window = text[match.end(): match.end() + 80]
        overall = re.search(r"overall[^0-9]{0,15}([4-9](?:\.[05])?)(?![\d])", window, re.IGNORECASE)
        if overall:
            return float(overall.group(1))
        plain = re.search(r"(?<![\d.])([4-9](?:\.[05])?)(?![\d])", window)
        if plain:
            return float(plain.group(1))
    return None


def _find_degree(text):
    """Degree the student is *aiming for*. Only set when the CV clearly says so."""
    intent = re.compile(
        r"(?:seeking|pursu\w+|apply\w*|admission|objective|interested in|aspir\w+|plan(?:ning)? to|"
        r"looking for|goal)[^.\n]{0,100}?\b(ph\.?\s?d\.?|doctoral|doctorate|master'?s?|m\.?sc\.?|msc|ms degree)",
        re.IGNORECASE,
    )
    match = intent.search(text)
    if not match:
        return None
    word = match.group(1).lower().replace(".", "").replace(" ", "")
    return "phd" if word in ("phd", "doctoral", "doctorate") else "masters"


def _find_field(text):
    degree = re.search(
        r"(?:b\.?\s?sc\.?|bsc|b\.?\s?eng\.?|bachelor(?:'s)?|b\.?\s?tech)[^\n,;]{0,25}?\b(?:in|of)\s+"
        r"([A-Za-z][A-Za-z &/\-]{3,60}?)(?=\s*(?:[,;(\n|\-–—]|specializ|major|\d{4}|$))",
        text, re.IGNORECASE,
    )
    if degree:
        return degree.group(1).strip(" -–—")[:100]
    lowered = text.lower()
    counts = [(lowered.count(word.lower()), -i, word) for i, word in enumerate(FIELD_WORDS)]
    counts = [c for c in counts if c[0] > 0]
    return max(counts)[2] if counts else None


def _find_skills(text):
    found = []
    for word in SKILL_WORDS:
        pattern = r"(?<![A-Za-z0-9+#.])" + re.escape(word) + r"(?![A-Za-z0-9+#])"
        # Single letters ("R", "C") match far too easily; require the exact capital letter.
        flags = 0 if len(word) <= 2 else re.IGNORECASE
        match = re.search(pattern, text, flags)
        if match:
            found.append((match.start(), word))
    found.sort()
    return "; ".join(word for _, word in found)[:500] or None


def _find_interests(text):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^\s*(?:research\s+interests?|areas?\s+of\s+interests?|research\s+areas?|interests?)\s*:?\s*(.*)$",
                    line, re.IGNORECASE):
            first = re.sub(r"^\s*[A-Za-z ]+?:", "", line, count=1).strip() if ":" in line else ""
            collected = [first] if first else []
            for follower in lines[index + 1: index + 8]:
                if not follower.strip() or _HEADING.match(follower):
                    if collected:
                        break
                    continue
                collected.append(follower.strip(" •-–·*"))
            joined = "; ".join(part for part in collected if part)
            joined = re.sub(r"\s*[,;]\s*", "; ", joined).strip("; ")
            if len(joined) >= 4:
                return joined[:500]
    lowered = text.lower()
    topics = sorted((lowered.find(topic), topic) for topic in TOPIC_WORDS if topic in lowered)
    topics = [t for _, t in topics][:8]
    return "; ".join(topics)[:500] or None


def parse_cv(text):
    """Return suggested profile values plus notes for the review page.

    ``values`` has the same keys as the profile form. ``found`` lists the keys that were
    detected, so the page can mark what came from the CV. ``notes`` are warnings.
    """
    values = {"cgpa": "", "ielts": "", "target_degree": "", "field": "",
              "research_interests": "", "skills": ""}
    notes = []

    cgpa, cgpa_note = _find_cgpa(text)
    if cgpa is not None:
        values["cgpa"] = f"{cgpa:g}"
    if cgpa_note:
        notes.append(cgpa_note)

    ielts = _find_ielts(text)
    if ielts is not None:
        values["ielts"] = f"{ielts:g}"

    values["target_degree"] = _find_degree(text) or ""
    values["field"] = _find_field(text) or ""
    values["skills"] = _find_skills(text) or ""
    values["research_interests"] = _find_interests(text) or ""

    found = [key for key, value in values.items() if value]
    return {"values": values, "found": found, "notes": notes}
