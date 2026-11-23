from app.services.evidence import split_sentences
from app.services.keyword_matcher import tokenize
from app.services.semantic_matcher import get_model

SOURCE_FIELDS = ("title", "field", "description", "requirements_text")
TOP_SENTENCES = 2
_cache = {}


def _value(opportunity, key):
    try:
        return opportunity[key]
    except (KeyError, IndexError):
        return None


def label_for(score):
    """Same rough thresholds as the ranking; they are assumptions, not tuned values."""
    if score >= 0.45:
        return "strong"
    if score >= 0.30:
        return "moderate"
    return "weak"


def interests_text(profile):
    parts = [profile.get("research_interests"), profile.get("field")]
    return ". ".join(p.strip() for p in parts if p and p.strip())


def project_sentences(opportunity):
    """Title, field and sentences of the description and requirements."""
    sentences = []
    for field in SOURCE_FIELDS:
        value = _value(opportunity, field)
        if not value:
            continue
        if field in ("title", "field"):
            sentences.append(value.strip())
        else:
            sentences.extend(split_sentences(value))
    seen, unique = set(), []
    for s in sentences:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def get_research_fit(profile, opportunity, use_model=True):
    """Compare a student's interests with a PhD project text.

    Returns None for non-PhD opportunities or when the student gave no interests.
    The result only describes how close the texts are. It does not judge admission chances.
    """
    if _value(opportunity, "degree_level") != "phd":
        return None
    text = interests_text(profile)
    if not text:
        return None

    sentences = project_sentences(opportunity)
    project_words = tokenize(" ".join(sentences))
    shared_terms = sorted(tokenize(text) & project_words)
    skills_overlap = sorted(tokenize(profile.get("skills") or "") & project_words)

    result = {"score": 0.0, "label": "weak", "matches": [],
              "shared_terms": shared_terms, "skills_overlap": skills_overlap}
    if not use_model or not sentences:
        return result

    from sentence_transformers import util
    model = get_model()
    key = _value(opportunity, "id")
    if key is not None and key in _cache:
        embeddings = _cache[key]
    else:
        embeddings = model.encode(sentences, convert_to_tensor=True)
        if key is not None:
            _cache[key] = embeddings

    query = model.encode(text, convert_to_tensor=True)
    scores = util.cos_sim(query, embeddings)[0]
    order = scores.argsort(descending=True)[:TOP_SENTENCES]
    matches = [{"sentence": sentences[int(i)], "score": max(0.0, float(scores[int(i)]))}
               for i in order]

    result["matches"] = matches
    result["score"] = matches[0]["score"] if matches else 0.0
    result["label"] = label_for(result["score"])
    return result