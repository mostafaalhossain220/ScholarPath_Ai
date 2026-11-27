import os

# Test the light (TF-IDF) mode so the tests also pass on machines
# without sentence-transformers. Must be set before the import below.
os.environ["FORCE_LIGHT_MATCHING"] = "1"

from app.services.ranking import rank_opportunities  # noqa: E402


def make_opportunity(id, title, field, degree_level="phd", country="UK", description=""):
    return {
        "id": id,
        "title": title,
        "field": field,
        "degree_level": degree_level,
        "country": country,
        "description": description,
        "requirements_text": "",
        "funding": "Fully funded",
        "min_cgpa": None,
        "min_ielts": None,
    }


def make_profile(**overrides):
    profile = {
        "target_degree": "phd",
        "cgpa": None,
        "ielts": None,
        "field": "Computer Science",
        "preferred_countries": "",
        "research_interests": "machine learning",
        "skills": "Python",
    }
    profile.update(overrides)
    return profile


OPPORTUNITIES = [
    make_opportunity(1, "PhD in Machine Learning", "Computer Science",
                     description="Research on deep learning and neural networks."),
    make_opportunity(2, "MBA in Marketing", "Business", degree_level="masters",
                     country="USA", description="Brand strategy and sales."),
]


def test_empty_profile_does_not_crash():
    profile = make_profile(field="", research_interests="", skills="")
    results = rank_opportunities(profile, OPPORTUNITIES)
    assert len(results) == len(OPPORTUNITIES)
    assert all(r["semantic"] == 0.0 for r in results)


def test_scores_are_between_zero_and_one():
    results = rank_opportunities(make_profile(), OPPORTUNITIES)
    for r in results:
        assert 0.0 <= r["semantic"] <= 1.0
        assert 0.0 <= r["final_score"] <= 1.0


def test_matching_field_ranks_higher():
    results = rank_opportunities(make_profile(), OPPORTUNITIES)
    titles = [r["opportunity"]["title"] for r in results]
    assert titles[0] == "PhD in Machine Learning"