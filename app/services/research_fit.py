from app.services.evidence import split_sentences
from app.services.keyword_matcher import tokenize
from app.services.semantic_matcher import HAS_MODEL, get_model

TOP_SENTENCES = 2
_cache = {}


def _value(opportunity, key):
    try:
        return opportunity[key]
    except (KeyError, IndexError):
        return None


def label_for(score):
    """Light (TF-IDF) mode would use lower thresholds because its scores are smaller.
    Both are assumptions, not tuned values."""
    strong, moderate = (0.45, 0.30) if HAS_MODEL else (0.20, 0.10)
    if score >= strong:
        return "strong"
    if score >= moderate:
        return "moderate"
    return "weak"


def interests_text(profile):
    """Only the research interests. A field name is a department, not a research topic."""
    return (profile.get("research_interests") or "").strip()


def project_sentences(opportunity):
    """Sentences of the description and requirements. Title and field are only labels."""
    sentences = []
    for field in ("description", "requirements_text"):
        value = _value(opportunity, field)
        if value:
            sentences.extend(split_sentences(value))
    seen, unique = set(), []
    for s in sentences:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def get_research_fit(profile, opportunity, use_model=True):
    """Compare a student's research interests with a PhD project description.

    Returns None for non-PhD opportunities, when the student gave no interests,
    or when the opportunity has no description to compare with.
    The result only describes how close the texts are. It does not judge admission chances.
    """
    if _value(opportunity, "degree_level") != "phd":
        return None
    text = interests_text(profile)
    if not text:
        return None

    sentences = project_sentences(opportunity)
    if not sentences:
        return None
    project_words = tokenize(" ".join(sentences))
    shared_terms = sorted(tokenize(text) & project_words)
    skills_overlap = sorted(tokenize(profile.get("skills") or "") & project_words)

    result = {"score": 0.0, "label": "weak", "matches": [],
              "shared_terms": shared_terms, "skills_overlap": skills_overlap}
    # Without the heavy model, return only shared terms and skills overlap.
    if not (use_model and HAS_MODEL):
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