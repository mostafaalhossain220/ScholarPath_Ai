import re

from app.services.semantic_matcher import get_model

# For each requirement: keywords are tried first (precise), meaning second (fallback).
REQUIREMENTS = {
    "CGPA": {
        "keywords": ["gpa", "cgpa", "grade", "honours", "honors", "second-class",
                     "2:1", "first-class", "distinction"],
        "query": "minimum GPA or grade required for admission",
    },
    "IELTS": {
        "keywords": ["ielts", "toefl", "english", "language proficiency", "language requirement"],
        "query": "English language test score such as IELTS or TOEFL",
    },
    "degree level": {
        "keywords": ["bachelor", "master", "undergraduate", "degree", "graduate"],
        "query": "required previous degree or qualification",
    },
    "funding": {
        "keywords": ["fund", "stipend", "scholarship", "tuition", "salary", "allowance"],
        "query": "funding, stipend or tuition support",
    },
}

SOURCE_FIELDS = ("requirements_text", "description", "funding")
MIN_SEMANTIC = 0.35   # assumption: should be tuned by checking real examples
_cache = {}


def _value(opportunity, key):
    try:
        return opportunity[key]
    except (KeyError, IndexError):
        return None


def split_sentences(text):
    """Split text into sentences and drop very short fragments."""
    if not text:
        return []
    parts = re.split(r"(?<=[.!?;])\s+|\n+", text.strip())
    return [p.strip()[:300] for p in parts if len(p.strip()) >= 15]


def candidate_sentences(opportunity):
    """All (source field, sentence) pairs of an opportunity."""
    candidates = []
    for field in SOURCE_FIELDS:
        for sentence in split_sentences(_value(opportunity, field)):
            candidates.append((field, sentence))
    return candidates


def _keyword_hits(sentence, keywords):
    lowered = sentence.lower()
    return sum(1 for k in keywords if re.search(r"\b" + re.escape(k), lowered))


def find_evidence(opportunity, use_semantic=True):
    """Return, for every requirement, the best supporting sentence or None."""
    candidates = candidate_sentences(opportunity)
    result = {}
    embeddings = None

    for name, rule in REQUIREMENTS.items():
        best = None
        best_hits = 0
        for field, sentence in candidates:
            hits = _keyword_hits(sentence, rule["keywords"])
            if hits > best_hits:
                best, best_hits = (field, sentence), hits

        if best:
            result[name] = {"sentence": best[1], "source": best[0],
                            "method": "keyword", "score": float(best_hits)}
            continue

        result[name] = {"sentence": None, "source": None, "method": None, "score": 0.0}
        if not (use_semantic and candidates):
            continue

        from sentence_transformers import util
        model = get_model()
        if embeddings is None:
            embeddings = model.encode([s for _, s in candidates], convert_to_tensor=True)
        query = model.encode(rule["query"], convert_to_tensor=True)
        scores = util.cos_sim(query, embeddings)[0]
        index = int(scores.argmax())
        if float(scores[index]) >= MIN_SEMANTIC:
            field, sentence = candidates[index]
            result[name] = {"sentence": sentence, "source": field,
                            "method": "semantic", "score": float(scores[index])}
    return result


def get_evidence(opportunity):
    """Same as find_evidence, remembered per opportunity id (the model is slow)."""
    key = _value(opportunity, "id")
    if key is None:
        return find_evidence(opportunity)
    if key not in _cache:
        _cache[key] = find_evidence(opportunity)
    return _cache[key]