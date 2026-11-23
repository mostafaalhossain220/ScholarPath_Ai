"""Rank opportunities for a profile that came from a CV.

Uses the semantic ranking (Sentence Transformers) when it is installed. On a computer
or server without it, a keyword-based ranking is used instead, so the CV feature
always works. The page tells the student which method was used.
"""
from app.services.eligibility import check_eligibility
from app.services.keyword_matcher import keyword_score

COUNTRY_WEIGHT = 0.2


def _split(text):
    return [p.strip().lower() for p in (text or "").replace(",", ";").split(";") if p.strip()]


def _student_text(profile):
    parts = [profile.get("research_interests"), profile.get("field"), profile.get("skills")]
    return ". ".join(p.strip() for p in parts if p and p.strip())


def _keyword_rank(profile, opportunities):
    text = _student_text(profile)
    preferred = _split(profile.get("preferred_countries"))
    results = []
    for opp in opportunities:
        opp_text = " ".join(p for p in [opp["title"], opp["field"], opp["description"]] if p)
        kw, matched = keyword_score(text, opp_text)
        country = (opp["country"] or "").lower()
        hit = [c for c in preferred if c in country]
        reasons = []
        if matched:
            reasons.append("Shared keywords with your CV: " + ", ".join(matched[:10]) + ".")
        else:
            reasons.append("No shared keywords with your CV were found.")
        if hit:
            reasons.append("Located in a country you prefer: " + ", ".join(hit) + ".")
        results.append({
            "opportunity": opp,
            "final_score": (1 - COUNTRY_WEIGHT) * kw + COUNTRY_WEIGHT * (1.0 if hit else 0.0),
            "country_hit": hit,
            "eligibility": check_eligibility(profile, opp),
            "reasons": reasons,
        })
    results.sort(key=lambda r: (r["eligibility"]["overall"] != "not_satisfied", r["final_score"]),
                 reverse=True)
    return results


def rank_for_profile(profile, opportunities):
    """Return (results, method) where method is 'semantic' or 'keyword'."""
    profile = dict(profile)
    opportunities = list(opportunities)
    try:
        from app.services.ranking import rank_opportunities
    except ImportError:
        return _keyword_rank(profile, opportunities), "keyword"
    return rank_opportunities(profile, opportunities), "semantic"
