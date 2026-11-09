from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    """Load the model once and reuse it (loading takes a few seconds)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def opportunity_text(opportunity):
    """The text of an opportunity that we compare with the student's interests."""
    parts = [opportunity["title"], opportunity["field"], opportunity["description"]]
    return ". ".join(p for p in parts if p)


def semantic_scores(student_text, opportunities):
    """Cosine similarity between the student's text and each opportunity."""
    if not opportunities:
        return []
    if not student_text or not student_text.strip():
        return [0.0] * len(opportunities)

    model = get_model()
    student_vec = model.encode(student_text, convert_to_tensor=True)
    opp_vecs = model.encode(
        [opportunity_text(o) for o in opportunities], convert_to_tensor=True
    )
    scores = util.cos_sim(student_vec, opp_vecs)[0]
    return [max(0.0, float(s)) for s in scores]