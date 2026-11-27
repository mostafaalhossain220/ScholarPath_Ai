import os

try:
    if os.environ.get("FORCE_LIGHT_MATCHING") == "1":
        raise ImportError("light matching forced for testing")
    from sentence_transformers import SentenceTransformer, util
    HAS_MODEL = True
except ImportError:
    HAS_MODEL = False

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    """Load the model once and reuse it (loading takes a few seconds)."""
    global _model
    if not HAS_MODEL:
        raise RuntimeError("sentence-transformers is not installed")
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def opportunity_text(opportunity):
    """The text of an opportunity that we compare with the student's interests."""
    parts = [opportunity["title"], opportunity["field"], opportunity["description"]]
    return ". ".join(p for p in parts if p)


def _tfidf_scores(student_text, opportunities):
    """Light fallback: TF-IDF cosine similarity (no heavy model needed)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    docs = [student_text] + [opportunity_text(o) for o in opportunities]
    try:
        matrix = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        ).fit_transform(docs)
    except ValueError:  # only stop words / empty vocabulary
        return [0.0] * len(opportunities)
    scores = cosine_similarity(matrix[0:1], matrix[1:])[0]
    return [max(0.0, float(s)) for s in scores]


def semantic_scores(student_text, opportunities):
    """Similarity between the student's text and each opportunity."""
    if not opportunities:
        return []
    if not student_text or not student_text.strip():
        return [0.0] * len(opportunities)

    if not HAS_MODEL:
        return _tfidf_scores(student_text, opportunities)

    model = get_model()
    student_vec = model.encode(student_text, convert_to_tensor=True)
    opp_vecs = model.encode(
        [opportunity_text(o) for o in opportunities], convert_to_tensor=True
    )
    scores = util.cos_sim(student_vec, opp_vecs)[0]
    return [max(0.0, float(s)) for s in scores]