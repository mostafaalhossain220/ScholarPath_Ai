import re

STOPWORDS = {
    "and", "the", "for", "with", "from", "into", "that", "this", "are",
    "was", "will", "has", "have", "can", "all", "any", "not", "but",
    "our", "your", "their", "its", "who", "which", "may", "must",
}


def tokenize(text):
    """Lowercase the text and return a set of meaningful words."""
    if not text:
        return set()
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def keyword_score(student_text, opportunity_text):
    """Share of the student's keywords that also appear in the opportunity.

    Returns (score between 0 and 1, sorted list of matched words).
    """
    student_words = tokenize(student_text)
    if not student_words:
        return 0.0, []
    matched = student_words & tokenize(opportunity_text)
    return len(matched) / len(student_words), sorted(matched)