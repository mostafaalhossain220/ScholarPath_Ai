from app.services.eligibility import check_eligibility
from app.services.keyword_matcher import keyword_score
from app.services.semantic_matcher import semantic_scores

SEMANTIC_WEIGHT = 0.8
COUNTRY_WEIGHT = 0.2


def split_list(text):
    """'UK; USA' -> ['uk', 'usa']"""
    return [p.strip().lower() for p in (text or "").replace(",", ";").split(";") if p.strip()]


def strength_label(score):
    """Rough labels. Thresholds should be tuned later with labelled examples."""
    if score >= 0.45:
        return "strong"
    if score >= 0.30:
        return "moderate"
    return "weak"


def student_text(profile):
    parts = [profile.get("research_interests"), profile.get("field"), profile.get("skills")]
    return ". ".join(p.strip() for p in parts if p and p.strip())


def rank_opportunities(profile, opportunities):
    """Rank opportunities for one student profile and explain each result.

    Opportunities that fail a requirement are listed after the others, not hidden.
    The score is for ordering only. It is not a chance of admission.
    """
    profile = dict(profile)
    opportunities = list(opportunities)
    text = student_text(profile)
    semantic = semantic_scores(text, opportunities)
    preferred = split_list(profile.get("preferred_countries"))

    results = []
    for opp, sem in zip(opportunities, semantic):
        opp_text = " ".join(p for p in [opp["title"], opp["field"], opp["description"]] if p)
        kw, matched = keyword_score(text, opp_text)

        opp_country = (opp["country"] or "").lower()
        country_hit = [c for c in preferred if c in opp_country]

        eligibility = check_eligibility(profile, opp)
        final = SEMANTIC_WEIGHT * sem + COUNTRY_WEIGHT * (1.0 if country_hit else 0.0)

        reasons = []
        if text:
            reasons.append(f"Research interest similarity is {strength_label(sem)} ({sem:.2f}).")
        else:
            reasons.append("Add research interests or a field to your profile to get similarity scores.")
        if matched:
            reasons.append("Shared keywords: " + ", ".join(matched) + ".")
        if country_hit:
            reasons.append("Located in a country you prefer: " + ", ".join(country_hit) + ".")

        results.append({
            "opportunity": opp,
            "semantic": sem,
            "keyword": kw,
            "final_score": final,
            "country_hit": country_hit,
            "eligibility": eligibility,
            "reasons": reasons,
        })

    results.sort(
        key=lambda r: (r["eligibility"]["overall"] != "not_satisfied", r["final_score"]),
        reverse=True,
    )
    return results