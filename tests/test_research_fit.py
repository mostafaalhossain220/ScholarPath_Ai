from app.services.research_fit import get_research_fit, label_for

PHD = {
    "id": 1,
    "degree_level": "phd",
    "title": "PhD on machine translation",
    "field": "Computer Science",
    "description": "Research on neural machine translation and multilingual language models. The project uses Python and PyTorch.",
    "requirements_text": None,
}


def test_masters_has_no_research_fit():
    opportunity = dict(PHD, degree_level="masters")
    assert get_research_fit({"research_interests": "machine translation"}, opportunity, use_model=False) is None


def test_no_interests_gives_none():
    assert get_research_fit({"research_interests": "", "field": ""}, PHD, use_model=False) is None


def test_shared_terms_and_skills_without_model():
    profile = {"research_interests": "neural machine translation", "field": "", "skills": "Python, Java"}
    fit = get_research_fit(profile, PHD, use_model=False)
    assert "machine" in fit["shared_terms"] and "translation" in fit["shared_terms"]
    assert fit["skills_overlap"] == ["python"]


def test_label_thresholds():
    assert label_for(0.5) == "strong"
    assert label_for(0.35) == "moderate"
    assert label_for(0.1) == "weak"